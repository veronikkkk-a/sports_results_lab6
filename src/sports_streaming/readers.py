"""Streaming CSV reader."""
import csv
import logging
from collections.abc import Iterator
from pathlib import Path
from sports_streaming.exceptions import DataImportError
logger = logging.getLogger(__name__)
REQUIRED = {"athlete", "sport", "result", "category", "timestamp"}

def read_csv_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            missing = REQUIRED - set(reader.fieldnames or ())
            if missing:
                raise DataImportError(f"CSV is missing columns: {', '.join(sorted(missing))}")
            for number, row in enumerate(reader, start=2):
                if None in row:
                    yield number, {"__malformed__": "too many columns"}
                else:
                    yield number, {key: value or "" for key, value in row.items()}
    except DataImportError:
        raise
    except (OSError, csv.Error, UnicodeError) as error:
        raise DataImportError(f"Cannot read CSV input: {path}") from error
