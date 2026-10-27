"""Import policies, statistics, and streaming analytics."""
import logging
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from sports_streaming.exceptions import RecordValidationError
from sports_streaming.models import AppConfig, SportsResult
from sports_streaming.readers import read_csv_rows
from sports_streaming.validators import parse_record
logger = logging.getLogger(__name__)

@dataclass(slots=True)
class ImportStatistics:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    result_sums: dict[str, float] = field(default_factory=dict)
    result_counts: dict[str, int] = field(default_factory=dict)
    best_by_sport: dict[str, SportsResult] = field(default_factory=dict)

@contextmanager
def logged_operation(name: str) -> Iterator[None]:
    logger.info("%s started", name)
    started = perf_counter()
    try:
        yield
    except Exception:
        logger.exception("%s failed", name)
        raise
    else:
        logger.info("%s completed in %.4f s", name, perf_counter() - started)

def import_results(config: AppConfig, stats: ImportStatistics,
                   errors: list[dict[str, object]]) -> Iterator[SportsResult]:
    for number, row in read_csv_rows(config.input_path):
        stats.total += 1
        try:
            record = parse_record(row, line_number=number, config=config)
        except RecordValidationError as error:
            stats.invalid += 1
            errors.append({"line_number": number, "field": error.field or "record", "error": str(error)})
            logger.warning("Invalid record at line %d (%s): %s", number, error.field or "record", error)
            if config.mode == "strict":
                raise
            continue
        stats.valid += 1
        stats.result_sums[record.sport] = stats.result_sums.get(record.sport, 0.0) + record.result
        stats.result_counts[record.sport] = stats.result_counts.get(record.sport, 0) + 1
        previous = stats.best_by_sport.get(record.sport)
        if previous is None or record.result < previous.result:
            stats.best_by_sport[record.sport] = record
        yield record

def filter_results(records: Iterable[SportsResult], *, sport: str | None = None,
                   category: str | None = None) -> Iterator[SportsResult]:
    for record in records:
        if (sport is None or record.sport == sport) and (category is None or record.category == category):
            yield record

def mean_result(records: Iterable[SportsResult]) -> float | None:
    count, total = 0, 0.0
    for record in records:
        count += 1
        total += record.result
    return total / count if count else None

def best_result(records: Iterable[SportsResult]) -> SportsResult | None:
    """Return the record with the smallest numeric result in the supplied event subset."""
    best: SportsResult | None = None
    for record in records:
        if best is None or record.result < best.result:
            best = record
    return best
