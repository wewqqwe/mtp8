"""Показание с запретом отрицательных значений."""

from __future__ import annotations


class Meter:
    def __init__(self, reading: int) -> None:
        self.reading = reading

    @property
    def reading(self) -> int:
        return self._reading

    @reading.setter
    def reading(self, value: int) -> None:
        if value < 0:
            raise ValueError("reading")
        self._reading = value
