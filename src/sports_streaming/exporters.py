"""Safe atomic exporters."""
import csv
import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path
from sports_streaming.exceptions import DataExportError
from sports_streaming.models import SportsResult

def _atomic_write(path: Path, writer) -> None:
    temp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            writer(stream)
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
    except Exception as error:
        if temp is not None:
            temp.unlink(missing_ok=True)
        if isinstance(error, OSError):
            raise DataExportError(f"Cannot atomically write output: {path}") from error
        raise

def export_json(records: Iterable[SportsResult], path: Path) -> int:
    count = 0
    def write(stream):
        nonlocal count
        stream.write("[\n")
        for record in records:
            if count:
                stream.write(",\n")
            json.dump(record.to_dict(), stream, ensure_ascii=False, indent=2)
            count += 1
        stream.write("\n]\n")
    _atomic_write(path, write)
    return count

def export_errors(errors: list[dict[str, object]], path: Path) -> int:
    fields = ["line_number", "field", "error"]
    def write(stream):
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(errors)
    _atomic_write(path, write)
    return len(errors)
