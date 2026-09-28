"""Счётчик (Meter) с property, сравнением и историей показаний."""

from __future__ import annotations

from osetrova.maths import clip


class Meter:
    """Показание прибора с единицей измерения и историей.

    Parameters:
        reading: начальное показание (≥ 0).
        unit: единица измерения (только чтение).
    """

    __slots__ = ("_reading", "_unit", "_history")

    def __init__(self, reading: float, unit: str = "шт") -> None:
        self._history: list[float] = []
        self._unit = unit
        self.reading = reading  # через setter — проверка + запись в историю

    # --- property reading ---------------------------------------------------

    @property
    def reading(self) -> float:
        return self._reading

    @reading.setter
    def reading(self, value: float) -> None:
        if value < 0:
            raise ValueError("reading не может быть отрицательным")
        self._reading = value
        self._history.append(value)

    # --- property unit (read-only) ------------------------------------------

    @property
    def unit(self) -> str:
        return self._unit

    # --- property history ---------------------------------------------------

    @property
    def history(self) -> list[float]:
        """Все предыдущие значения reading (включая текущее)."""
        return list(self._history)

    # --- dunder-методы ------------------------------------------------------

    def __repr__(self) -> str:
        return f"Meter({self._reading}, unit={self._unit!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Meter):
            return NotImplemented
        return self._reading == other._reading

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Meter):
            return NotImplemented
        return self._reading < other._reading

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Meter):
            return NotImplemented
        return self._reading <= other._reading

    # --- бизнес-методы ------------------------------------------------------

    def delta(self, other: Meter) -> float:
        """Абсолютная разница между *self* и *other*."""
        return abs(self._reading - other._reading)

    def clamp(self, low: float, high: float) -> None:
        """Ограничивает текущее показание отрезком [low, high] (in-place)."""
        self.reading = clip(self._reading, low, high)
