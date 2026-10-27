import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock
import pytest
from sports_streaming.async_ranking import fetch_ranking
from sports_streaming.config import load_config
from sports_streaming.exporters import export_errors, export_json
from sports_streaming.exceptions import RecordValidationError
from sports_streaming.models import SportsResult
from sports_streaming.services import ImportStatistics, import_results

HEADER = "athlete,sport,result,category,timestamp"
VALID = "Olena,running,12.4,senior,2026-10-20T09:15:00"

def make_config_file(folder: Path, input_file: Path) -> Path:
    config = folder / "config.yaml"
    config.write_text(f'''input:\n  path: {input_file}\noutput:\n  path: {folder / 'output.json'}\n  error_path: {folder / 'errors.csv'}\nprocessing:\n  mode: tolerant\n  allowed_sports: [running, swimming]\n  allowed_categories: [senior, junior]\n  result_rules:\n    running: {{min: 0, max: 100}}\n    swimming: {{min: 0, max: 100}}\n  timestamp_format: "%Y-%m-%dT%H:%M:%S"\nlogging:\n  level: INFO\n  path: {folder / 'logs/app.log'}\n''', encoding="utf-8")
    return config

@pytest.mark.integration
def test_csv_validation_to_json_and_error_csv(tmp_path, app_config):
    source = tmp_path / "sports.csv"
    source.write_text(HEADER + "\n" + VALID + "\n" + "Bad,running,nope,senior,2026-10-20T09:30:00\n", encoding="utf-8")
    config = replace(app_config, input_path=source)
    stats = ImportStatistics(); errors = []
    count = export_json(import_results(config, stats, errors), config.output_path)
    export_errors(errors, config.error_path)
    exported = json.loads(config.output_path.read_text(encoding="utf-8"))
    assert count == 1 and exported[0]["athlete"] == "Olena"
    assert (stats.total, stats.valid, stats.invalid) == (2, 1, 1)
    assert "Result must be numeric" in config.error_path.read_text(encoding="utf-8")

@pytest.mark.integration
def test_strict_failure_preserves_previous_json_and_cleans_temp(tmp_path, app_config):
    source = tmp_path / "strict.csv"
    source.write_text(HEADER + "\n" + VALID + "\n" + "Bad,running,nope,senior,2026-10-20T09:30:00\n", encoding="utf-8")
    target = tmp_path / "previous.json"; target.write_text("PREVIOUS", encoding="utf-8")
    config = replace(app_config, input_path=source, output_path=target, mode="strict")
    errors = []; stats = ImportStatistics()
    with pytest.raises(RecordValidationError):
        export_json(import_results(config, stats, errors), target)
    export_errors(errors, config.error_path)
    assert target.read_text(encoding="utf-8") == "PREVIOUS"
    assert list(tmp_path.glob(".*.tmp")) == []
    assert len(errors) == 1

@pytest.mark.integration
@pytest.mark.asyncio
async def test_external_provider_ranking_integration(result_factory):
    provider = AsyncMock()
    provider.fetch_results.return_value = [result_factory(result=12), result_factory(athlete="Fast", result=9)]
    ranking = await fetch_ranking(provider, "running", top_n=2)
    assert [row.athlete for row in ranking] == ["Fast", "Olena Koval"]
    provider.fetch_results.assert_awaited_once_with("running")

@pytest.mark.integration
def test_cli_runs_config_to_atomic_outputs(tmp_path, monkeypatch):
    source = tmp_path / "input.csv"
    source.write_text(HEADER + "\n" + VALID + "\n", encoding="utf-8")
    cfg = make_config_file(tmp_path, source)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["sports-streaming", "--config", str(cfg)])
    from sports_streaming.main import main
    main()
    assert json.loads((tmp_path / "output.json").read_text(encoding="utf-8"))[0]["athlete"] == "Olena"
    assert (tmp_path / "errors.csv").exists()
    assert (tmp_path / "logs" / "app.log").exists()
