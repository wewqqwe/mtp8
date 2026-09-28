"""Тесты лабораторной №8, вариант 3.

Структура (TDD-стиль — тесты определяют контракт):
  - test_calc_*     — калькулятор (maths.py)
  - test_meter_*    — счётчик с property (meter.py)
  - test_repo_*     — шаблон Repository (repos.py), параметризация двумя бэкендами
  - test_async_*    — asyncio (jobs.py)
  - test_cli_*      — интеграционные (main.py через subprocess)
  - test_package_*  — импорт пакета
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import pytest

import osetrova
from osetrova.jobs import (
    _double,
    fetch_sim,
    producer_consumer,
    run_parallel,
    run_pipeline,
    run_sequential,
    run_two,
    run_with_timeout,
)
from osetrova.maths import CalcError, clip, evaluate, safe_div
from osetrova.meter import Meter
from osetrova.repos import (
    MemoryNoteRepo,
    MemoryNotes,
    NoteRepo,
    PairNotes,
    SqliteNoteRepo,
    publish,
)

ROOT = Path(__file__).resolve().parents[1]


# ===== КАЛЬКУЛЯТОР (TDD) ====================================================

class TestCalc:
    """Тесты написаны ДО реализации (red → green → refactor)."""

    def test_clip_within(self) -> None:
        assert clip(5, 0, 10) == 5

    def test_clip_below(self) -> None:
        assert clip(-2, 0, 10) == 0

    def test_clip_above(self) -> None:
        assert clip(15, 0, 10) == 10

    def test_clip_invalid_bounds(self) -> None:
        with pytest.raises(ValueError):
            clip(5, 10, 0)

    def test_safe_div_ok(self) -> None:
        assert safe_div(10, 2) == 5.0

    def test_safe_div_zero(self) -> None:
        with pytest.raises(CalcError, match="деление на ноль"):
            safe_div(1, 0)

    def test_evaluate_add(self) -> None:
        assert evaluate(2, "+", 3) == 5.0

    def test_evaluate_sub(self) -> None:
        assert evaluate(10, "-", 4) == 6.0

    def test_evaluate_mul(self) -> None:
        assert evaluate(3, "*", 7) == 21.0

    def test_evaluate_div(self) -> None:
        assert evaluate(15, "/", 3) == 5.0

    def test_evaluate_div_zero(self) -> None:
        with pytest.raises(CalcError):
            evaluate(1, "/", 0)

    def test_evaluate_power(self) -> None:
        assert evaluate(2, "^", 10) == 1024.0

    def test_evaluate_power_zero_neg(self) -> None:
        with pytest.raises(CalcError, match="0 в отрицательной"):
            evaluate(0, "^", -1)

    def test_evaluate_mod(self) -> None:
        assert evaluate(17, "%", 5) == 2.0

    def test_evaluate_mod_zero(self) -> None:
        with pytest.raises(CalcError):
            evaluate(5, "%", 0)

    def test_evaluate_sqrt(self) -> None:
        assert evaluate(16, "sqrt") == 4.0

    def test_evaluate_sqrt_negative(self) -> None:
        with pytest.raises(CalcError, match="корень из отрицательного"):
            evaluate(-4, "sqrt")

    def test_evaluate_unknown_op(self) -> None:
        with pytest.raises(CalcError, match="неизвестная операция"):
            evaluate(1, "??", 2)


# ===== METER =================================================================

class TestMeter:
    def test_create_default_unit(self) -> None:
        m = Meter(42)
        assert m.reading == 42
        assert m.unit == "шт"

    def test_create_custom_unit(self) -> None:
        m = Meter(100, unit="кг")
        assert m.unit == "кг"

    def test_reject_negative(self) -> None:
        with pytest.raises(ValueError):
            Meter(-1)

    def test_setter_reject_negative(self) -> None:
        m = Meter(5)
        with pytest.raises(ValueError):
            m.reading = -10
        assert m.reading == 5  # не изменилось

    def test_repr(self) -> None:
        m = Meter(42, unit="шт")
        assert repr(m) == "Meter(42, unit='шт')"

    def test_eq(self) -> None:
        assert Meter(10) == Meter(10)
        assert Meter(10) != Meter(20)

    def test_lt(self) -> None:
        assert Meter(5) < Meter(10)
        assert not (Meter(10) < Meter(5))

    def test_le(self) -> None:
        assert Meter(5) <= Meter(5)
        assert Meter(5) <= Meter(10)

    def test_delta(self) -> None:
        assert Meter(100).delta(Meter(30)) == 70
        assert Meter(30).delta(Meter(100)) == 70  # абсолютное

    def test_clamp(self) -> None:
        m = Meter(50)
        m.clamp(0, 30)
        assert m.reading == 30

    def test_clamp_below(self) -> None:
        m = Meter(2)
        m.clamp(5, 100)
        assert m.reading == 5

    def test_history(self) -> None:
        m = Meter(10)
        m.reading = 20
        m.reading = 30
        assert m.history == [10, 20, 30]

    def test_history_after_clamp(self) -> None:
        m = Meter(50)
        m.clamp(0, 30)
        assert m.history == [50, 30]


# ===== REPOSITORY (параметризация двумя бэкендами) ==========================

@pytest.fixture(params=["memory", "sqlite"])
def repo(request: pytest.FixtureRequest, tmp_path: Path) -> NoteRepo:
    """Один и тот же набор тестов для MemoryNoteRepo и SqliteNoteRepo."""
    if request.param == "memory":
        return MemoryNoteRepo()
    db_file = tmp_path / "test.db"
    return SqliteNoteRepo(str(db_file))


class TestRepo:
    def test_add_and_get(self, repo: NoteRepo) -> None:
        note = repo.add("Привет")
        assert note.id >= 1
        assert note.text == "Привет"
        fetched = repo.get(note.id)
        assert fetched is not None
        assert fetched.text == "Привет"

    def test_count(self, repo: NoteRepo) -> None:
        assert repo.count() == 0
        repo.add("a")
        repo.add("b")
        assert repo.count() == 2

    def test_delete(self, repo: NoteRepo) -> None:
        note = repo.add("удалить")
        assert repo.delete(note.id) is True
        assert repo.get(note.id) is None
        assert repo.count() == 0

    def test_delete_nonexistent(self, repo: NoteRepo) -> None:
        assert repo.delete(999) is False

    def test_update(self, repo: NoteRepo) -> None:
        note = repo.add("старый")
        updated = repo.update(note.id, "новый")
        assert updated is not None
        assert updated.text == "новый"

    def test_update_nonexistent(self, repo: NoteRepo) -> None:
        assert repo.update(999, "x") is None

    def test_list_all(self, repo: NoteRepo) -> None:
        repo.add("a")
        repo.add("b")
        repo.add("c")
        assert len(repo.list()) == 3

    def test_list_pinned_filter(self, repo: NoteRepo) -> None:
        repo.add("обычная", pinned=False)
        repo.add("важная", pinned=True)
        repo.add("ещё обычная", pinned=False)
        assert len(repo.list(pinned=True)) == 1
        assert len(repo.list(pinned=False)) == 2
        assert repo.list(pinned=True)[0].text == "важная"

    def test_get_nonexistent(self, repo: NoteRepo) -> None:
        assert repo.get(999) is None


# ===== Совместимость со старым API ===========================================

class TestLegacy:
    def test_publish_memory_notes(self) -> None:
        assert publish(MemoryNotes(), ["a", "b"]) == ["a", "b"]

    def test_publish_pair_notes(self) -> None:
        assert publish(PairNotes(), ["a", "b"]) == ["a", "b"]

    def test_publish_new_repo(self) -> None:
        repo = MemoryNoteRepo()
        result = publish(repo, ["x", "y"])
        assert result == ["x", "y"]


# ===== ASYNCIO ===============================================================

class TestAsync:
    def test_double_compat(self) -> None:
        assert asyncio.run(_double(5)) == 10

    def test_run_two_compat(self) -> None:
        assert asyncio.run(run_two(3, 4)) == [6, 8]

    def test_fetch_sim(self) -> None:
        result = asyncio.run(fetch_sim("https://example.com", 0.01))
        assert result["url"] == "https://example.com"
        assert result["status"] == 200

    def test_parallel_faster_than_sequential(self) -> None:
        tasks = [("a", 0.1), ("b", 0.1), ("c", 0.1)]

        t0 = time.perf_counter()
        asyncio.run(run_parallel(tasks))
        t_par = time.perf_counter() - t0

        t0 = time.perf_counter()
        asyncio.run(run_sequential(tasks))
        t_seq = time.perf_counter() - t0

        # Параллельный запуск должен быть ощутимо быстрее
        assert t_par < t_seq * 0.8

    def test_run_with_timeout_ok(self) -> None:
        result = asyncio.run(run_with_timeout(fetch_sim("x", 0.01), 1.0))
        assert result is not None
        assert result["url"] == "x"

    def test_run_with_timeout_expired(self) -> None:
        result = asyncio.run(run_with_timeout(fetch_sim("x", 5.0), 0.05))
        assert result is None

    def test_pipeline(self) -> None:
        async def double(x: float) -> float:
            return x * 2

        async def add_ten(x: float) -> float:
            return x + 10

        result = asyncio.run(run_pipeline(5, double, add_ten))
        assert result == 20  # 5*2=10, 10+10=20

    def test_producer_consumer(self) -> None:
        results = asyncio.run(producer_consumer([1, 2, 3], workers=2))
        assert sorted(results) == [2, 4, 6]

    def test_producer_consumer_strings(self) -> None:
        results = asyncio.run(producer_consumer(["a", "b"], workers=2))
        assert sorted(results) == ["a_done", "b_done"]


# ===== CLI ===================================================================

class TestCli:
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "main.py", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_no_args_compat(self) -> None:
        r = self._run()
        assert r.returncode == 0
        assert "10" in r.stdout  # clip(15,0,10)
        assert "[6, 8]" in r.stdout

    def test_calc_add(self) -> None:
        r = self._run("calc", "2", "+", "3")
        assert r.returncode == 0
        assert "5.0" in r.stdout

    def test_calc_sqrt(self) -> None:
        r = self._run("calc", "16", "sqrt")
        assert r.returncode == 0
        assert "4.0" in r.stdout

    def test_calc_div_zero(self) -> None:
        r = self._run("calc", "1", "/", "0")
        assert r.returncode != 0

    def test_meter(self) -> None:
        r = self._run("meter", "42")
        assert r.returncode == 0
        assert "Meter(42" in r.stdout

    def test_notes_demo(self) -> None:
        r = self._run("notes", "demo")
        assert r.returncode == 0
        assert "Первая" in r.stdout
        assert "Важная" in r.stdout

    def test_async_pipeline(self) -> None:
        r = self._run("async", "pipeline")
        assert r.returncode == 0
        assert "20" in r.stdout


# ===== ИМПОРТ ПАКЕТА ========================================================

class TestPackage:
    def test_package_import(self) -> None:
        assert hasattr(osetrova, "maths")
        assert hasattr(osetrova, "meter")
        assert hasattr(osetrova, "repos")
        assert hasattr(osetrova, "jobs")

    def test_clip_via_package(self) -> None:
        assert osetrova.maths.clip(1, 0, 2) == 1
