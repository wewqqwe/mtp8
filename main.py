"""CLI-интерфейс пакета osetrova.

Подкоманды:
    calc   — калькулятор (evaluate)
    meter  — создание объекта Meter
    notes  — работа с заметками (add / list)
    async  — демонстрация asyncio (--parallel / --pipeline / --prodcon)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from osetrova.jobs import (
    fetch_sim,
    producer_consumer,
    run_parallel,
    run_pipeline,
    run_sequential,
    run_two,
    run_with_timeout,
)
from osetrova.maths import CalcError, clip, evaluate
from osetrova.meter import Meter
from osetrova.repos import MemoryNoteRepo, MemoryNotes, PairNotes, publish


# ---------------------------------------------------------------------------
# Подкоманды
# ---------------------------------------------------------------------------

def cmd_calc(args: argparse.Namespace) -> None:
    """Вычислить выражение через evaluate."""
    left = args.left
    op = args.op
    right = args.right if args.right is not None else 0.0
    try:
        result = evaluate(left, op, right)
        print(result)
    except CalcError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_meter(args: argparse.Namespace) -> None:
    """Создать Meter и показать repr."""
    unit = args.unit if args.unit else "шт"
    m = Meter(args.value, unit=unit)
    print(m)


def cmd_notes(args: argparse.Namespace) -> None:
    """Управление заметками (in-memory)."""
    repo = MemoryNoteRepo()
    if args.action == "add":
        note = repo.add(args.text)
        print(f"Добавлена заметка №{note.id}: {note.text}")
    elif args.action == "list":
        # Для демонстрации добавим пару записей
        if repo.count() == 0:
            print("Хранилище пусто. Добавьте заметки: main.py notes add \"текст\"")
    elif args.action == "demo":
        repo.add("Первая заметка")
        repo.add("Важная!", pinned=True)
        repo.add("Третья заметка")
        for n in repo.list():
            pin = " 📌" if n.pinned else ""
            print(f"  #{n.id}: {n.text}{pin}")
        print(f"Всего: {repo.count()}")


def cmd_async(args: argparse.Namespace) -> None:
    """Демонстрация asyncio."""
    tasks = [
        ("https://example.com/a", 0.15),
        ("https://example.com/b", 0.10),
        ("https://example.com/c", 0.12),
    ]

    if args.mode == "parallel":
        t0 = time.perf_counter()
        results = asyncio.run(run_parallel(tasks))
        elapsed = time.perf_counter() - t0
        print(f"Параллельно ({len(results)} задач): {elapsed:.3f} с")
        for r in results:
            print(f"  {r['url']} → {r['status']}")

    elif args.mode == "sequential":
        t0 = time.perf_counter()
        results = asyncio.run(run_sequential(tasks))
        elapsed = time.perf_counter() - t0
        print(f"Последовательно ({len(results)} задач): {elapsed:.3f} с")
        for r in results:
            print(f"  {r['url']} → {r['status']}")

    elif args.mode == "pipeline":
        async def stage_double(x: float) -> float:
            await asyncio.sleep(0)
            return x * 2

        async def stage_add_ten(x: float) -> float:
            await asyncio.sleep(0)
            return x + 10

        result = asyncio.run(run_pipeline(5, stage_double, stage_add_ten))
        print(f"Pipeline: 5 → ×2 → +10 = {result}")

    elif args.mode == "prodcon":
        results = asyncio.run(producer_consumer([1, 2, 3, 4, 5], workers=2))
        print(f"Producer-consumer: {sorted(results)}")

    elif args.mode == "compat":
        print("clip", clip(15, 0, 10))
        m = Meter(3)
        print("meter", m.reading)
        print("memory", publish(MemoryNotes(), ["a", "b"]))
        print("pairs", publish(PairNotes(), ["a", "b"]))
        print("async", asyncio.run(run_two(3, 4)))


# ---------------------------------------------------------------------------
# Парсер
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Лабораторная №8 — экосистема Python (вариант 3)",
    )
    sub = parser.add_subparsers(dest="command", help="подкоманда")

    # calc
    p_calc = sub.add_parser("calc", help="калькулятор")
    p_calc.add_argument("left", type=float, help="левый операнд")
    p_calc.add_argument(
        "op", choices=["+", "-", "*", "/", "^", "%", "sqrt"],
        help="операция",
    )
    p_calc.add_argument("right", type=float, nargs="?", default=None,
                        help="правый операнд (не нужен для sqrt)")

    # meter
    p_meter = sub.add_parser("meter", help="создать Meter")
    p_meter.add_argument("value", type=float, help="показание")
    p_meter.add_argument("--unit", default="шт", help="единица измерения")

    # notes
    p_notes = sub.add_parser("notes", help="заметки")
    p_notes.add_argument("action", choices=["add", "list", "demo"],
                         help="действие")
    p_notes.add_argument("text", nargs="?", default="", help="текст заметки")

    # async
    p_async = sub.add_parser("async", help="демонстрация asyncio")
    p_async.add_argument(
        "mode",
        choices=["parallel", "sequential", "pipeline", "prodcon", "compat"],
        help="режим запуска",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        # Без аргументов — совместимый вывод (как было раньше)
        print("clip", clip(15, 0, 10))
        m = Meter(3)
        print("meter", m.reading)
        print("memory", publish(MemoryNotes(), ["a", "b"]))
        print("pairs", publish(PairNotes(), ["a", "b"]))
        print("async", asyncio.run(run_two(3, 4)))
        return

    dispatch = {
        "calc": cmd_calc,
        "meter": cmd_meter,
        "notes": cmd_notes,
        "async": cmd_async,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
