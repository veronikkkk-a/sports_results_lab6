"""Immutable domain and config models."""
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True, slots=True)
class SportsResult:
    athlete: str
    sport: str
    result: float
    category: str
    timestamp: datetime
    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["timestamp"] = self.timestamp.isoformat()
        return value

@dataclass(frozen=True, slots=True)
class AppConfig:
    input_path: Path
    output_path: Path
    error_path: Path
    mode: str
    allowed_sports: frozenset[str]
    allowed_categories: frozenset[str]
    result_rules: dict[str, tuple[float, float]]
    timestamp_format: str
    log_level: str
    log_path: Path
