"""Демонстрация пакета osetrova."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from osetrova.jobs import run_two
from osetrova.maths import clip
from osetrova.meter import Meter
from osetrova.repos import MemoryNotes, PairNotes, publish


def main() -> None:
    print("clip", clip(15, 0, 10))
    meter = Meter(3)
    print("meter", meter.reading)
    print("memory", publish(MemoryNotes(), ["a", "b"]))
    print("pairs", publish(PairNotes(), ["a", "b"]))
    print("async", asyncio.run(run_two(3, 4)))


if __name__ == "__main__":
    main()
