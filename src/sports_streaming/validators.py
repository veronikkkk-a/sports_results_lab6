"""Validation at the external data boundary."""
import math
from datetime import datetime
from sports_streaming.exceptions import RecordValidationError
from sports_streaming.models import AppConfig, SportsResult

def parse_record(row: dict[str, str], *, line_number: int, config: AppConfig) -> SportsResult:
    if "__malformed__" in row:
        raise RecordValidationError(row["__malformed__"], line_number=line_number)
    athlete, sport, category = (row.get(key, "").strip() for key in ("athlete", "sport", "category"))
    sport, category = sport.lower(), category.lower()
    if not athlete:
        raise RecordValidationError("Athlete name is required", line_number=line_number, field="athlete")
    if sport not in config.allowed_sports:
        raise RecordValidationError("Sport is not allowed", line_number=line_number, field="sport")
    if category not in config.allowed_categories:
        raise RecordValidationError("Category is not allowed", line_number=line_number, field="category")
    try:
        result = float(row["result"])
    except (KeyError, ValueError) as error:
        raise RecordValidationError("Result must be numeric", line_number=line_number, field="result") from error
    if not math.isfinite(result) or result < 0:
        raise RecordValidationError("Result must be finite and non-negative", line_number=line_number, field="result")
    minimum, maximum = config.result_rules[sport]
    if not minimum <= result <= maximum:
        raise RecordValidationError(f"Result outside configured range {minimum}..{maximum}", line_number=line_number, field="result")
    try:
        timestamp = datetime.strptime(row["timestamp"].strip(), config.timestamp_format)
    except (KeyError, ValueError) as error:
        raise RecordValidationError("Timestamp has invalid format", line_number=line_number, field="timestamp") from error
    return SportsResult(athlete, sport, result, category, timestamp)
