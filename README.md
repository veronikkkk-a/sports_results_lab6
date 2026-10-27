# Лабораторна робота №6 — автоматизоване тестування

Варіант 9: система обліку спортивних результатів. Проєкт продовжує пакет із ЛР №5 і додає test suite на pytest, pytest-cov та pytest-asyncio.

## Запуск

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -v --cov=sports_streaming --cov-branch --cov-report=term-missing --cov-report=html
```

Тести поділені на `tests/unit` та `tests/integration`. Вони ізолюють файли через `tmp_path`, зовнішній стан — через fixtures, `monkeypatch`, `Mock` та `AsyncMock`. Coverage налаштований на гілки з мінімальним порогом 80%.
