"""Selection helpers for the sports results stream."""
from collections.abc import Iterable, Iterator
from sports_streaming.models import SportsResult

def filter_results(records: Iterable[SportsResult], *, sport: str | None = None,
                   category: str | None = None) -> Iterator[SportsResult]:
    for record in records:
        if (sport is None or record.sport == sport) and (category is None or record.category == category):
            yield record
