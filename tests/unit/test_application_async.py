from unittest.mock import AsyncMock, Mock
import pytest
from sports_streaming.application import ResultApplication
from sports_streaming.async_ranking import fetch_ranking
from sports_streaming.repositories import InMemoryResultRepository, ResultRepository
from sports_streaming.notifications import ResultNotifier

@pytest.mark.parametrize("sport,result", [("running",0.0),("running",100.0)], ids=["zero","positive"])
def test_repository_saves_and_filters(result_factory, sport, result):
    repo = InMemoryResultRepository(); record = result_factory(sport=sport, result=result)
    assert repo.save(record) == "result-1"
    assert repo.list_all(sport) == [record]
    assert repo.list_all("swimming") == []

def test_application_uses_mock_return_value_and_checks_interactions(result_factory):
    repository = Mock(spec=ResultRepository); repository.save.return_value = "R-44"
    notifier = Mock(spec=ResultNotifier)
    service = ResultApplication(repository, notifier)
    result = result_factory()
    assert service.register(result) == "R-44"
    repository.save.assert_called_once_with(result)
    notifier.notify.assert_called_once_with("Sports result R-44 recorded")

def test_repository_failure_uses_side_effect_and_skips_notification(result_factory):
    repository = Mock(spec=ResultRepository); repository.save.side_effect = OSError("storage unavailable")
    notifier = Mock(spec=ResultNotifier)
    with pytest.raises(OSError, match="unavailable"):
        ResultApplication(repository, notifier).register(result_factory())
    repository.save.assert_called_once()
    notifier.notify.assert_not_called()

@pytest.mark.asyncio
async def test_async_provider_is_awaited_and_ranked(result_factory):
    provider = AsyncMock()
    provider.fetch_results.return_value = [
        result_factory(athlete="A", result=15), result_factory(athlete="B", result=10),
        result_factory(athlete="Swimmer", sport="swimming", result=50, category="junior")]
    ranked = await fetch_ranking(provider, "running", top_n=1)
    assert [item.athlete for item in ranked] == ["B"]
    provider.fetch_results.assert_awaited_once_with("running")

@pytest.mark.asyncio
async def test_async_provider_failure_propagates(result_factory):
    provider = AsyncMock(); provider.fetch_results.side_effect = TimeoutError("provider timed out")
    with pytest.raises(TimeoutError, match="timed out"):
        await fetch_ranking(provider, "running")
    provider.fetch_results.assert_awaited_once()
