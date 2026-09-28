"""Обрезка числа по включительным границам."""

from __future__ import annotations


def clip(value: int, low: int, high: int) -> int:
    if value < low:
        return low
    if value > high:
        return high
    return value
