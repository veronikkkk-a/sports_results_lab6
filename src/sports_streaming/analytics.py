"""Bounded ranking and sequential result analysis."""
from collections.abc import Iterable, Iterator
from heapq import nsmallest
from itertools import pairwise
from sports_streaming.models import SportsResult

def rank_results(records: Iterable[SportsResult], top_n: int = 10) -> list[SportsResult]:
    """Return the N smallest numeric results using bounded selection memory."""
    if top_n < 1:
        raise ValueError("top_n must be positive")
    return nsmallest(top_n, records, key=lambda item: item.result)

def pairwise_changes(records: Iterable[SportsResult]) -> Iterator[tuple[SportsResult, SportsResult, float]]:
    """Yield adjacent result changes only when sport and category are comparable."""
    for previous, current in pairwise(records):
        if (previous.sport, previous.category) == (current.sport, current.category):
            yield previous, current, current.result - previous.result
