"""Fixed-size batches for downstream processing."""
from collections.abc import Iterable, Iterator
from itertools import islice
from sports_streaming.models import SportsResult

def batches(records: Iterable[SportsResult], size: int) -> Iterator[tuple[SportsResult, ...]]:
    if size < 1:
        raise ValueError("batch size must be positive")
    iterator = iter(records)
    while batch := tuple(islice(iterator, size)):
        yield batch
