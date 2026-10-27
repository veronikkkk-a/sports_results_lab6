"""Failure branches of the CLI are translated to controlled exit codes."""
import pytest

HEADER = "athlete,sport,result,category,timestamp"
VALID = "Olena,running,12.4,senior,2026-10-20T09:15:00"

def make_config_file(folder, input_file):
    config = folder / "config.yaml"
    config.write_text(f'''input:\n  path: {input_file}\noutput:\n  path: {folder / 'output.json'}\n  error_path: {folder / 'errors.csv'}\nprocessing:\n  mode: tolerant\n  allowed_sports: [running, swimming]\n  allowed_categories: [senior, junior]\n  result_rules:\n    running: {{min: 0, max: 100}}\n    swimming: {{min: 0, max: 100}}\n  timestamp_format: "%Y-%m-%dT%H:%M:%S"\nlogging:\n  level: INFO\n  path: {folder / 'logs/app.log'}\n''', encoding="utf-8")
    return config

def test_cli_negative_limit_exits_one(tmp_path, monkeypatch):
    source = tmp_path / "input.csv"; source.write_text(HEADER + "\n" + VALID + "\n", encoding="utf-8")
    config = make_config_file(tmp_path, source)
    monkeypatch.chdir(tmp_path); monkeypatch.setattr("sys.argv", ["app", "--config", str(config), "--limit", "-1"])
    from sports_streaming.main import main
    with pytest.raises(SystemExit) as exc: main()
    assert exc.value.code == 1

def test_cli_strict_error_preserves_old_output(tmp_path, monkeypatch):
    source = tmp_path / "input.csv"
    source.write_text(HEADER + "\n" + VALID + "\n" + "Bad,running,nope,senior,2026-10-20T09:30:00\n", encoding="utf-8")
    config = make_config_file(tmp_path, source)
    config.write_text(config.read_text(encoding="utf-8").replace("mode: tolerant", "mode: strict"), encoding="utf-8")
    previous = tmp_path / "output.json"; previous.write_text("previous", encoding="utf-8")
    monkeypatch.chdir(tmp_path); monkeypatch.setattr("sys.argv", ["app", "--config", str(config)])
    from sports_streaming.main import main
    with pytest.raises(SystemExit) as exc: main()
    assert exc.value.code == 1
    assert previous.read_text(encoding="utf-8") == "previous"
    assert "Result must be numeric" in (tmp_path / "errors.csv").read_text(encoding="utf-8")

def test_cli_handles_logging_io_failure(tmp_path, monkeypatch):
    source = tmp_path / "input.csv"; source.write_text(HEADER + "\n" + VALID + "\n", encoding="utf-8")
    config = make_config_file(tmp_path, source)
    monkeypatch.setattr("sys.argv", ["app", "--config", str(config)])
    monkeypatch.setattr("sports_streaming.main.configure_logging", lambda *_: (_ for _ in ()).throw(OSError("disk")))
    from sports_streaming.main import main
    with pytest.raises(SystemExit) as exc: main()
    assert exc.value.code == 1


def test_cli_positive_limit_processes_only_requested_rows(tmp_path, monkeypatch):
    source = tmp_path / "input.csv"
    source.write_text(HEADER + "\n" + VALID + "\n" + "Danylo,running,13,senior,2026-10-20T09:30:00\n", encoding="utf-8")
    config = make_config_file(tmp_path, source)
    monkeypatch.chdir(tmp_path); monkeypatch.setattr("sys.argv", ["app", "--config", str(config), "--limit", "1"])
    from sports_streaming.main import main
    main()
    import json
    assert len(json.loads((tmp_path / "output.json").read_text(encoding="utf-8"))) == 1
