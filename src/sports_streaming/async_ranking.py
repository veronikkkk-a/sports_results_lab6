"""Async boundary for importing remote sport results."""
from collections.abc import Sequence
from typing import Protocol
from sports_streaming.analytics import rank_results
from sports_streaming.models import SportsResult

class ExternalResultsProvider(Protocol):
    async def fetch_results(self, sport: str) -> Sequence[SportsResult]: ...

async def fetch_ranking(provider: ExternalResultsProvider, sport: str, top_n: int = 10) -> list[SportsResult]:
    records = await provider.fetch_results(sport)
    return rank_results((item for item in records if item.sport == sport), top_n=top_n)
