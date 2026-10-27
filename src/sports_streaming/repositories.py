"""Contracts for persisted sports results."""
from collections.abc import Sequence
from typing import Protocol
from sports_streaming.models import SportsResult

class ResultRepository(Protocol):
    def save(self, result: SportsResult) -> str: ...
    def list_all(self, sport: str | None = None) -> Sequence[SportsResult]: ...

class InMemoryResultRepository:
    def __init__(self) -> None:
        self._records: list[SportsResult] = []
    def save(self, result: SportsResult) -> str:
        self._records.append(result)
        return f"result-{len(self._records)}"
    def list_all(self, sport: str | None = None) -> list[SportsResult]:
        return [item for item in self._records if sport is None or item.sport == sport]
