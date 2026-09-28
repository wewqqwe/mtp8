"""Калькулятор с диспетчеризацией операций и обработкой крайних случаев.

Демонстрирует TDD-подход: каждая функция сначала покрывается тестом,
затем реализуется (red → green → refactor).
"""

from __future__ import annotations

import math
from typing import Callable


class CalcError(Exception):
    """Ошибка вычисления: деление на ноль, корень из отрицательного и т. д."""


def clip(value: float, low: float, high: float) -> float:
    """Ограничивает *value* включительными границами [low, high]."""
    if low > high:
        raise ValueError(f"low ({low}) > high ({high})")
    if value < low:
        return low
    if value > high:
        return high
    return value


def safe_div(a: float, b: float) -> float:
    """Безопасное деление: при *b* == 0 бросает :class:`CalcError`."""
    if b == 0:
        raise CalcError("деление на ноль")
    return a / b


def _sqrt(a: float, _b: float) -> float:
    """Квадратный корень из *a* (второй аргумент игнорируется)."""
    if a < 0:
        raise CalcError("корень из отрицательного числа")
    return math.sqrt(a)


def _power(a: float, b: float) -> float:
    """Возведение *a* в степень *b* с проверкой 0 ** (отрицательное)."""
    if a == 0 and b < 0:
        raise CalcError("0 в отрицательной степени")
    return a ** b


def _mod(a: float, b: float) -> float:
    """Остаток от деления *a* на *b*."""
    if b == 0:
        raise CalcError("деление на ноль (остаток)")
    return a % b


OPERATIONS: dict[str, Callable[[float, float], float]] = {
    "+":    lambda a, b: a + b,
    "-":    lambda a, b: a - b,
    "*":    lambda a, b: a * b,
    "/":    safe_div,
    "^":    _power,
    "%":    _mod,
    "sqrt": _sqrt,
}


def evaluate(left: float, op: str, right: float = 0.0) -> float:
    """Вычисляет ``left op right`` по словарю *OPERATIONS*.

    Для унарных операций (sqrt) *right* не используется.

    Raises:
        CalcError: при ошибочных операндах или неизвестной операции.
    """
    func = OPERATIONS.get(op)
    if func is None:
        raise CalcError(f"неизвестная операция: {op!r}")
    return func(left, right)
