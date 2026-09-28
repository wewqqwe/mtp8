"""Две конкурентные задачи."""

from __future__ import annotations

import asyncio


async def _double(number: int) -> int:
    await asyncio.sleep(0)
    return number * 2


async def run_two(x: int, y: int) -> list[int]:
    left, right = await asyncio.gather(_double(x), _double(y))
    return [left, right]
