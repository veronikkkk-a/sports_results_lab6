"""Shared fixtures for unit and integration tests."""
from datetime import datetime
from pathlib import Path
from dataclasses import replace
import pytest
from sports_streaming.models import AppConfig, SportsResult
from sports_streaming.repositories import InMemoryResultRepository

@pytest.fixture
def result_factory():
    def create(*, athlete="Olena Koval", sport="running", result=12.4,
               category="senior", timestamp=None):
        return SportsResult(athlete, sport, result, category,
                            timestamp or datetime(2026, 10, 20, 9, 15))
    return create

@pytest.fixture
def app_config(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("athlete,sport,result,category,timestamp\n", encoding="utf-8")
    return AppConfig(source, tmp_path / "out" / "results.json", tmp_path / "out" / "errors.csv",
        "tolerant", frozenset({"running", "swimming", "cycling"}),
        frozenset({"junior", "senior", "masters"}),
        {"running": (0.0, 100000.0), "swimming": (0.0, 100000.0), "cycling": (0.0, 100000.0)},
        "%Y-%m-%dT%H:%M:%S", "INFO", tmp_path / "logs" / "app.log")

@pytest.fixture
def configured_csv(tmp_path):
    path = tmp_path / "sports.csv"
    path.write_text(
        "athlete,sport,result,category,timestamp\n"
        "Olena,running,12.4,senior,2026-10-20T09:15:00\n"
        "Danylo,running,13.0,senior,2026-10-20T09:30:00\n"
        "Bad,swimming,wrong,junior,2026-10-20T10:00:00\n",
        encoding="utf-8")
    return path

@pytest.fixture
def result_records(result_factory):
    return [result_factory(result=12.4), result_factory(athlete="Danylo", result=13.0),
            result_factory(athlete="Maksym", sport="swimming", result=58.2, category="junior")]

@pytest.fixture
def repository():
    store = InMemoryResultRepository()
    yield store
    store._records.clear()
