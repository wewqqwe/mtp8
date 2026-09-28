"""Шаблон Repository: один вызывающий код, две реализации."""

from __future__ import annotations


class NoteBook:
    def add(self, text: str) -> None:
        raise NotImplementedError

    def items(self) -> list[str]:
        raise NotImplementedError


class MemoryNotes(NoteBook):
    def __init__(self) -> None:
        self._lines: list[str] = []

    def add(self, text: str) -> None:
        self._lines.append(text)

    def items(self) -> list[str]:
        return list(self._lines)


class PairNotes(NoteBook):
    def __init__(self) -> None:
        self._rows: dict[int, str] = {}

    def add(self, text: str) -> None:
        self._rows[len(self._rows) + 1] = text

    def items(self) -> list[str]:
        return [self._rows[key] for key in sorted(self._rows)]


def publish(repo: NoteBook, lines: list[str]) -> list[str]:
    for line in lines:
        repo.add(line)
    return repo.items()
