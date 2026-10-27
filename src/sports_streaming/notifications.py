"""Notification boundary for recorded result events."""
from typing import Protocol
class ResultNotifier(Protocol):
    def notify(self, message: str) -> None: ...
