import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import pytest
import yaml
from sports_streaming.config import load_config, validate_config
from sports_streaming.exceptions import ConfigurationError, DataImportError, DataExportError, RecordValidationError
from sports_streaming.exporters import export_errors, export_json
from sports_streaming.logging_config import configure_logging
from sports_streaming.models import AppConfig
from sports_streaming.readers import read_csv_rows
from sports_streaming.services import ImportStatistics, import_results, logged_operation
from sports_streaming.filters import filter_results as filter_module_results

FIELDS = "athlete,sport,result,category,timestamp"
ROW = "Olena,running,12.4,senior,2026-10-20T09:15:00"

def write_yaml(path: Path, input_path: Path) -> Path:
    path.write_text(f'''input:\n  path: {input_path}\noutput:\n  path: {path.parent / 'result.json'}\n  error_path: {path.parent / 'errors.csv'}\nprocessing:\n  mode: tolerant\n  allowed_sports: [running, swimming, cycling]\n  allowed_categories: [junior, senior, masters]\n  result_rules:\n    running: {{min: 0, max: 100000}}\n    swimming: {{min: 0, max: 100000}}\n    cycling: {{min: 0, max: 100000}}\n  timestamp_format: "%Y-%m-%dT%H:%M:%S"\nlogging:\n  level: INFO\n  path: {path.parent / 'app.log'}\n''', encoding="utf-8")
    return path

def test_csv_reader_yields_rows_lazily(configured_csv):
    rows = read_csv_rows(configured_csv)
    assert iter(rows) is rows
    assert next(rows)[0] == 2

def test_csv_reader_rejects_missing_headers(tmp_path):
    path = tmp_path / "bad.csv"; path.write_text("athlete,result\nA,1\n", encoding="utf-8")
    with pytest.raises(DataImportError, match="missing columns"):
        list(read_csv_rows(path))

def test_csv_reader_marks_extra_columns(tmp_path):
    path = tmp_path / "extra.csv"; path.write_text(FIELDS + "\n" + ROW + ",unexpected\n", encoding="utf-8")
    number, row = next(read_csv_rows(path))
    assert number == 2 and row["__malformed__"] == "too many columns"

def test_csv_reader_wraps_missing_file(tmp_path):
    with pytest.raises(DataImportError) as exc:
        list(read_csv_rows(tmp_path / "missing.csv"))
    assert isinstance(exc.value.__cause__, FileNotFoundError)

def test_load_yaml_configuration(tmp_path):
    source = tmp_path / "in.csv"; source.write_text(FIELDS + "\n", encoding="utf-8")
    config = load_config(write_yaml(tmp_path / "config.yaml", source))
    assert config.mode == "tolerant" and config.input_path == source

def test_bad_yaml_has_chained_cause(tmp_path):
    path = tmp_path / "bad.yaml"; path.write_text("input: [", encoding="utf-8")
    with pytest.raises(ConfigurationError) as exc:
        load_config(path)
    assert isinstance(exc.value.__cause__, yaml.YAMLError)

def test_missing_config_has_chained_cause(tmp_path):
    with pytest.raises(ConfigurationError) as exc:
        load_config(tmp_path / "absent.yaml")
    assert isinstance(exc.value.__cause__, FileNotFoundError)

def test_missing_input_is_fail_fast(tmp_path):
    config = AppConfig(tmp_path / "no.csv", tmp_path / "o.json", tmp_path / "e.csv", "tolerant",
        frozenset({"running"}), frozenset({"senior"}), {"running":(0, 10)}, "%Y-%m-%dT%H:%M:%S", "INFO", tmp_path / "a.log")
    with pytest.raises(ConfigurationError, match="Input file"):
        validate_config(config)

def test_mode_environment_override_uses_monkeypatch(tmp_path, monkeypatch):
    source = tmp_path / "in.csv"; source.write_text(FIELDS + "\n", encoding="utf-8")
    config_path = write_yaml(tmp_path / "config.yaml", source)
    monkeypatch.setenv("SPORTS_RESULTS_MODE", "strict")
    assert load_config(config_path).mode == "strict"

def test_invalid_mode_fails_config_validation(app_config):
    with pytest.raises(ConfigurationError, match="strict or tolerant"):
        validate_config(replace(app_config, mode="fast"))

def test_invalid_range_fails_config_validation(app_config):
    rules = {**app_config.result_rules, "running": (20.0, 10.0)}
    with pytest.raises(ConfigurationError, match="range"):
        validate_config(replace(app_config, result_rules=rules))

def test_tolerant_import_updates_statistics_and_error_list(app_config, configured_csv):
    stats = ImportStatistics(); errors = []
    config = replace(app_config, input_path=configured_csv)
    records = list(import_results(config, stats, errors))
    assert (stats.total, stats.valid, stats.invalid) == (3, 2, 1)
    assert len(records) == 2 and errors[0]["field"] == "result"

def test_strict_import_stops_at_first_invalid(app_config, configured_csv):
    stats = ImportStatistics()
    with pytest.raises(RecordValidationError, match="numeric"):
        list(import_results(replace(app_config, input_path=configured_csv, mode="strict"), stats, []))
    assert stats.invalid == 1 and stats.total == 3

def test_json_export_writes_serializable_results(tmp_path, result_records):
    path = tmp_path / "nested" / "result.json"
    assert export_json(result_records[:2], path) == 2
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["timestamp"] == "2026-10-20T09:15:00"

def test_error_export_writes_csv(tmp_path):
    path = tmp_path / "errors.csv"
    assert export_errors([{"line_number": 4, "field": "result", "error": "bad"}], path) == 1
    assert "result" in path.read_text(encoding="utf-8")

def test_atomic_export_preserves_existing_file_on_replace_failure(tmp_path, result_records, monkeypatch):
    target = tmp_path / "previous.json"; target.write_text("old", encoding="utf-8")
    def fail_replace(_self, _target):
        raise OSError("disk is read-only")
    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(DataExportError, match="atomically"):
        export_json(result_records[:1], target)
    assert target.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".*.tmp")) == []

def test_logging_configuration_creates_utf8_file(tmp_path):
    log_path = tmp_path / "logs" / "app.log"
    configure_logging("INFO", log_path)
    import logging
    logging.getLogger("test-log").info("тест")
    for handler in logging.getLogger().handlers: handler.flush()
    assert "тест" in log_path.read_text(encoding="utf-8")

def test_logged_operation_logs_failure_and_reraises(caplog):
    with pytest.raises(RuntimeError, match="boom"):
        with logged_operation("test op"):
            raise RuntimeError("boom")
    assert "test op failed" in caplog.text



def test_filter_module_can_select_category(result_records):
    assert len(list(filter_module_results(result_records, category="senior"))) == 2
