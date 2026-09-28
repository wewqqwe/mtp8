"""Шаблон Repository: единый контракт для двух бэкендов (память и SQLite).

Предметная область — текстовые заметки с пометкой «закреплено».
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# Модель
# ---------------------------------------------------------------------------

@dataclass
class Note:
    """Заметка с уникальным id, текстом и флагом закрепления."""

    id: int
    text: str
    pinned: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Абстрактный репозиторий
# ---------------------------------------------------------------------------

class NoteRepo(ABC):
    """Контракт хранилища заметок."""

    @abstractmethod
    def add(self, text: str, *, pinned: bool = False) -> Note:
        """Создать заметку и вернуть её."""

    @abstractmethod
    def get(self, note_id: int) -> Note | None:
        """Получить заметку по *note_id* или ``None``."""

    @abstractmethod
    def list(self, *, pinned: bool | None = None) -> list[Note]:
        """Все заметки; если *pinned* задан — фильтрация."""

    @abstractmethod
    def delete(self, note_id: int) -> bool:
        """Удалить заметку. Возвращает ``True`` если существовала."""

    @abstractmethod
    def update(self, note_id: int, text: str) -> Note | None:
        """Обновить текст заметки. ``None`` если не найдена."""

    @abstractmethod
    def count(self) -> int:
        """Количество заметок в хранилище."""


# ---------------------------------------------------------------------------
# In-memory реализация
# ---------------------------------------------------------------------------

class MemoryNoteRepo(NoteRepo):
    """Хранит заметки в обычном списке (автоинкремент id)."""

    def __init__(self) -> None:
        self._notes: list[Note] = []
        self._seq = 0

    def _next_id(self) -> int:
        self._seq += 1
        return self._seq

    def add(self, text: str, *, pinned: bool = False) -> Note:
        note = Note(id=self._next_id(), text=text, pinned=pinned)
        self._notes.append(note)
        return note

    def get(self, note_id: int) -> Note | None:
        return next((n for n in self._notes if n.id == note_id), None)

    def list(self, *, pinned: bool | None = None) -> list[Note]:
        if pinned is None:
            return list(self._notes)
        return [n for n in self._notes if n.pinned is pinned]

    def delete(self, note_id: int) -> bool:
        for i, n in enumerate(self._notes):
            if n.id == note_id:
                self._notes.pop(i)
                return True
        return False

    def update(self, note_id: int, text: str) -> Note | None:
        note = self.get(note_id)
        if note is None:
            return None
        note.text = text
        return note

    def count(self) -> int:
        return len(self._notes)


# ---------------------------------------------------------------------------
# SQLite реализация
# ---------------------------------------------------------------------------

class SqliteNoteRepo(NoteRepo):
    """Хранит заметки в файле SQLite (или ``:memory:``)."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  text TEXT NOT NULL,"
            "  pinned INTEGER NOT NULL DEFAULT 0,"
            "  created_at TEXT NOT NULL"
            ")"
        )
        self._conn.commit()

    # -- helpers --

    def _row_to_note(self, row: tuple) -> Note:  # type: ignore[type-arg]
        return Note(
            id=row[0],
            text=row[1],
            pinned=bool(row[2]),
            created_at=datetime.fromisoformat(row[3]),
        )

    # -- CRUD --

    def add(self, text: str, *, pinned: bool = False) -> Note:
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "INSERT INTO notes (text, pinned, created_at) VALUES (?, ?, ?)",
            (text, int(pinned), now),
        )
        self._conn.commit()
        return self._row_to_note(
            self._conn.execute(
                "SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
        )

    def get(self, note_id: int) -> Note | None:
        row = self._conn.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        return self._row_to_note(row) if row else None

    def list(self, *, pinned: bool | None = None) -> list[Note]:
        if pinned is None:
            rows = self._conn.execute("SELECT * FROM notes ORDER BY id").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM notes WHERE pinned = ? ORDER BY id",
                (int(pinned),),
            ).fetchall()
        return [self._row_to_note(r) for r in rows]

    def delete(self, note_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def update(self, note_id: int, text: str) -> Note | None:
        cur = self._conn.execute(
            "UPDATE notes SET text = ? WHERE id = ?", (text, note_id)
        )
        self._conn.commit()
        if cur.rowcount == 0:
            return None
        return self.get(note_id)

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]

    def close(self) -> None:
        self._conn.close()


# ---------------------------------------------------------------------------
# Совместимость с оригинальным API
# ---------------------------------------------------------------------------

class NoteBook:
    """Устаревший интерфейс (оставлен для обратной совместимости)."""

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
        return [self._rows[k] for k in sorted(self._rows)]


def publish(repo: NoteBook | NoteRepo, lines: Sequence[str]) -> list[str]:
    """Записывает *lines* в репозиторий и возвращает все записи.

    Поддерживает и старый (NoteBook), и новый (NoteRepo) интерфейс.
    """
    if isinstance(repo, NoteBook):
        for line in lines:
            repo.add(line)
        return repo.items()
    # NoteRepo
    for line in lines:
        repo.add(line)
    return [n.text for n in repo.list()]
