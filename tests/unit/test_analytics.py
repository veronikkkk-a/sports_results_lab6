import pytest
from sports_streaming.analytics import pairwise_changes, rank_results
from sports_streaming.models import SportsResult
from sports_streaming.services import best_result, filter_results, mean_result
from sports_streaming.batches import batches

def test_rank_returns_lowest_n(result_records):
    ranked = rank_results(result_records, top_n=2)
    assert [item.result for item in ranked] == [12.4, 13.0]

def test_rank_rejects_zero_count(result_records):
    with pytest.raises(ValueError, match="positive"):
        rank_results(result_records, top_n=0)

def test_pairwise_change_for_same_event(result_factory):
    first, second = result_factory(result=12.0), result_factory(athlete="B", result=12.7)
    pair = list(pairwise_changes([first, second]))
    assert len(pair) == 1
    assert pair[0][2] == pytest.approx(0.7)

def test_pairwise_skips_different_sports(result_factory):
    first = result_factory()
    other = result_factory(sport="swimming", category="junior", result=55)
    assert list(pairwise_changes([first, other])) == []

def test_filter_by_sport_and_category(result_records):
    found = list(filter_results(result_records, sport="running", category="senior"))
    assert len(found) == 2
    assert all(item.sport == "running" for item in found)

def test_filter_without_criteria_returns_all(result_records):
    assert list(filter_results(result_records)) == result_records

def test_mean_uses_approx(result_records):
    assert mean_result(result_records[:2]) == pytest.approx(12.7)

def test_mean_empty_is_none():
    assert mean_result([]) is None

def test_best_result_empty_is_none():
    assert best_result([]) is None

def test_best_result_returns_smallest(result_records):
    assert best_result(result_records[:2]).athlete == "Olena Koval"

def test_batches_split_and_keep_final_partial(result_records):
    assert [len(batch) for batch in batches(result_records, 2)] == [2, 1]

def test_batches_reject_nonpositive_size(result_records):
    with pytest.raises(ValueError, match="positive"):
        list(batches(result_records, 0))
