"""Application service coordinating repository and notifier interactions."""
from sports_streaming.models import SportsResult
from sports_streaming.notifications import ResultNotifier
from sports_streaming.repositories import ResultRepository

class ResultApplication:
    def __init__(self, repository: ResultRepository, notifier: ResultNotifier) -> None:
        self.repository = repository
        self.notifier = notifier
    def register(self, result: SportsResult) -> str:
        result_id = self.repository.save(result)
        self.notifier.notify(f"Sports result {result_id} recorded")
        return result_id
