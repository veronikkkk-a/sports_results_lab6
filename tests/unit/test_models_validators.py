from dataclasses import replace
from datetime import datetime
import math
import pytest
from sports_streaming.exceptions import RecordValidationError
from sports_streaming.models import SportsResult
from sports_streaming.validators import parse_record

BASE = {"athlete":" Athlete A ","sport":"running","result":"12.5","category":"senior",
        "timestamp":"2026-10-20T09:15:00"}

def test_sports_result_serializes_timestamp(result_factory):
    record = result_factory()
    assert record.to_dict()["timestamp"] == "2026-10-20T09:15:00"
    assert record.to_dict()["athlete"] == "Olena Koval"

def test_parse_record_normalizes_text(app_config):
    result = parse_record(BASE, line_number=2, config=app_config)
    assert result.athlete == "Athlete A"
    assert result.sport == "running"
    assert result.result == 12.5

@pytest.mark.parametrize("value", ["0", "100000"], ids=["minimum", "maximum"])
def test_result_boundaries_are_valid(value, app_config):
    assert parse_record({**BASE, "result": value}, line_number=2, config=app_config).result == float(value)

@pytest.mark.parametrize("changes,field", [
    ({"athlete":""}, "athlete"),
    ({"sport":"skiing"}, "sport"),
    ({"category":"open"}, "category"),
    ({"result":"bad"}, "result"),
    ({"result":"-0.01"}, "result"),
    ({"result":"nan"}, "result"),
    ({"result":"100001"}, "result"),
    ({"timestamp":"yesterday"}, "timestamp"),
], ids=["empty-athlete","unknown-sport","unknown-category","not-number","negative","nan","above-max","bad-time"])
def test_invalid_record_fields_raise_domain_error(changes, field, app_config):
    with pytest.raises(RecordValidationError) as exc:
        parse_record({**BASE, **changes}, line_number=17, config=app_config)
    assert exc.value.field == field
    assert exc.value.line_number == 17

def test_numeric_error_preserves_cause(app_config):
    with pytest.raises(RecordValidationError) as exc:
        parse_record({**BASE, "result":"wrong"}, line_number=4, config=app_config)
    assert isinstance(exc.value.__cause__, ValueError)

def test_missing_result_preserves_key_error(app_config):
    row = dict(BASE); row.pop("result")
    with pytest.raises(RecordValidationError) as exc:
        parse_record(row, line_number=3, config=app_config)
    assert isinstance(exc.value.__cause__, KeyError)

def test_malformed_row_marker_is_rejected(app_config):
    with pytest.raises(RecordValidationError, match="too many columns"):
        parse_record({"__malformed__":"too many columns"}, line_number=5, config=app_config)

def test_timestamp_is_a_datetime(result_factory):
    assert isinstance(result_factory().timestamp, datetime)
