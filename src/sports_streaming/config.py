"""YAML configuration loading and fail-fast validation."""
import os
from pathlib import Path
from typing import Any
import yaml
from sports_streaming.exceptions import ConfigurationError
from sports_streaming.models import AppConfig

def load_config(path: Path) -> AppConfig:
    try:
        with path.open("r", encoding="utf-8") as stream:
            raw: Any = yaml.safe_load(stream)
    except OSError as error:
        raise ConfigurationError(f"Cannot read configuration: {path}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML configuration: {path}") from error
    try:
        if not isinstance(raw, dict):
            raise TypeError("Top-level YAML value must be a mapping")
        inp, out, proc, log = (raw[key] for key in ("input", "output", "processing", "logging"))
        rules = {str(sport): (float(bounds["min"]), float(bounds["max"]))
                 for sport, bounds in proc["result_rules"].items()}
        config = AppConfig(Path(inp["path"]), Path(out["path"]), Path(out["error_path"]),
            os.getenv("SPORTS_RESULTS_MODE", str(proc["mode"])).lower(), frozenset(map(str, proc["allowed_sports"])),
            frozenset(map(str, proc["allowed_categories"])), rules,
            str(proc["timestamp_format"]), str(log["level"]).upper(), Path(log["path"]))
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ConfigurationError("Configuration structure or value is invalid") from error
    validate_config(config)
    return config

def validate_config(config: AppConfig) -> None:
    if config.mode not in {"strict", "tolerant"}:
        raise ConfigurationError("processing.mode must be strict or tolerant")
    if not config.allowed_sports or not config.allowed_categories:
        raise ConfigurationError("Allowed sports and categories cannot be empty")
    if set(config.result_rules) != set(config.allowed_sports):
        raise ConfigurationError("Every allowed sport must have one result rule")
    for sport, (minimum, maximum) in config.result_rules.items():
        if minimum > maximum:
            raise ConfigurationError(f"Invalid result range for {sport}")
    if config.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError("Unsupported logging level")
    if not config.input_path.is_file():
        raise ConfigurationError(f"Input file does not exist: {config.input_path}")

