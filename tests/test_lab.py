from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

import osetrova
from osetrova.jobs import run_two
from osetrova.maths import clip
from osetrova.meter import Meter
from osetrova.repos import MemoryNotes, PairNotes, publish

ROOT = Path(__file__).resolve().parents[1]


def test_package_import() -> None:
    assert osetrova.maths.clip(1, 0, 2) == 1


def test_clip_bounds() -> None:
    assert clip(15, 0, 10) == 10
    assert clip(-2, 0, 10) == 0
    assert clip(4, 0, 10) == 4


def test_meter_rejects_negative() -> None:
    meter = Meter(4)
    assert meter.reading == 4
    with pytest.raises(ValueError):
        meter.reading = -1
    assert meter.reading == 4
    with pytest.raises(ValueError):
        Meter(-5)


def test_publish_works_for_both_repositories() -> None:
    assert publish(MemoryNotes(), ["a", "b"]) == ["a", "b"]
    assert publish(PairNotes(), ["a", "b"]) == ["a", "b"]


def test_asyncio_returns_both() -> None:
    assert asyncio.run(run_two(3, 4)) == [6, 8]


def test_cli() -> None:
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "10" in result.stdout
    assert "[6, 8]" in result.stdout
