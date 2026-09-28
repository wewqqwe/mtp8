# Лабораторная работа №8. Экосистема Python

**Осетрова Алина Романовна, группа 221141, вариант 3**

Дисциплина «Методы и технологии программирования» (часть 1).

---

## Структура пакета

```
mtp8/
├── main.py                 # CLI-интерфейс (argparse + subparsers)
├── pyproject.toml           # конфигурация проекта и pytest
├── requirements.txt         # зависимости
├── src/
│   └── osetrova/
│       ├── __init__.py      # реэкспорт модулей
│       ├── maths.py         # калькулятор с TDD
│       ├── meter.py         # класс Meter с property
│       ├── repos.py         # шаблон Repository
│       └── jobs.py          # asyncio-задачи
└── tests/
    └── test_lab.py          # 45+ тестов
```

---

## Задания варианта 3

| № | Задание | Модуль | Статус |
|---|---------|--------|--------|
| 1 | Функция с pytest (TDD) | `maths.py` | ✅ |
| 2 | Структура `src/пакет` | `src/osetrova/` | ✅ |
| 3 | Класс с property | `meter.py` | ✅ |
| 4 | Шаблон Repository | `repos.py` | ✅ |
| 5 | asyncio | `jobs.py` | ✅ |

---

## 1. Калькулятор (`maths.py`) — TDD

### Что реализовано

- **`clip(value, low, high)`** — ограничение числа включительными границами.
- **`safe_div(a, b)`** — деление с выбросом `CalcError` при делении на ноль.
- **`evaluate(left, op, right)`** — диспетчеризация через словарь `OPERATIONS`.
- **`CalcError`** — собственный класс исключения.

### Поддерживаемые операции

| Операция | Символ | Пример |
|----------|--------|--------|
| Сложение | `+` | `evaluate(2, "+", 3)` → `5.0` |
| Вычитание | `-` | `evaluate(10, "-", 4)` → `6.0` |
| Умножение | `*` | `evaluate(3, "*", 7)` → `21.0` |
| Деление | `/` | `evaluate(15, "/", 3)` → `5.0` |
| Степень | `^` | `evaluate(2, "^", 10)` → `1024.0` |
| Остаток | `%` | `evaluate(17, "%", 5)` → `2.0` |
| Корень | `sqrt` | `evaluate(16, "sqrt")` → `4.0` |

### Крайние случаи (каждый покрыт тестом)

- Деление на ноль → `CalcError`
- Корень из отрицательного числа → `CalcError`
- `0 ^ (-1)` → `CalcError`
- Остаток от деления на ноль → `CalcError`
- Неизвестная операция → `CalcError`
- `clip` с перевёрнутыми границами → `ValueError`

### TDD-цикл

1. **Red** — написан тест `test_evaluate_sqrt_negative`, функции `evaluate` ещё нет → тест падает.
2. **Green** — реализована `evaluate` с обработкой случая → тест проходит.
3. **Refactor** — вынесены вспомогательные `_sqrt`, `_power`, `_mod` для читаемости.

---

## 2. Класс Meter (`meter.py`)

### Поля и свойства

| Свойство | Тип | Описание |
|----------|-----|----------|
| `reading` | `float` (property) | Текущее показание, setter запрещает отрицательные |
| `unit` | `str` (read-only) | Единица измерения |
| `history` | `list[float]` (read-only) | Все предыдущие значения `reading` |

### Методы

- `__repr__` — `Meter(42, unit='шт')`
- `__eq__` — сравнение по `reading`
- `__lt__`, `__le__` — упорядочение по `reading`
- `delta(other)` — абсолютная разница показаний
- `clamp(low, high)` — ограничить показание через `clip`

### Пример

```python
m = Meter(50, unit="кг")
m.clamp(0, 30)      # reading стало 30
m.reading = 10
print(m.history)     # [50, 30, 10]
print(m.delta(Meter(100)))  # 90.0
```

---

## 3. Шаблон Repository (`repos.py`)

### Модель данных

```python
@dataclass
class Note:
    id: int
    text: str
    pinned: bool = False
    created_at: datetime = ...
```

### ABC `NoteRepo`

Контракт: `add`, `get`, `list`, `delete`, `update`, `count`.

### Две реализации

| Класс | Хранилище | Особенности |
|-------|-----------|-------------|
| `MemoryNoteRepo` | `list` в памяти | автоинкремент id |
| `SqliteNoteRepo` | файл SQLite | SQL через `sqlite3` |

### Преимущество паттерна

Один и тот же набор тестов запускается для **обеих** реализаций через `pytest.fixture(params=["memory", "sqlite"])`. Если тесты проходят для обоих бэкендов — контракт соблюдён. Подмена хранилища не требует изменения клиентского кода.

### Обратная совместимость

Старые классы `NoteBook`, `MemoryNotes`, `PairNotes` и функция `publish` сохранены.

---

## 4. Asyncio (`jobs.py`)

### Реализованные сценарии

| Функция | Что делает |
|---------|------------|
| `fetch_sim(url, delay)` | Имитация HTTP-запроса с задержкой |
| `run_parallel(tasks)` | Параллельный запуск через `gather` |
| `run_sequential(tasks)` | Последовательный запуск (для сравнения) |
| `run_with_timeout(coro, seconds)` | Обёртка с `wait_for`, `None` при таймауте |
| `run_pipeline(data, *stages)` | Конвейер async-функций |
| `producer_consumer(items, workers)` | Классический паттерн с `asyncio.Queue` |

### Тест скорости

```python
def test_parallel_faster_than_sequential():
    # 3 задачи по 0.1с:
    #   параллельно ≈ 0.1с
    #   последовательно ≈ 0.3с
    assert t_par < t_seq * 0.8
```

### Producer-consumer

Один producer кладёт элементы в `asyncio.Queue`, несколько consumer-ов обрабатывают параллельно. Обработка: числа удваиваются, строки получают суффикс `_done`.

---

## Запуск

### Установка зависимостей

```bash
uv venv --python 3.12 .venv
uv pip install pytest pytest-asyncio
```

### Тесты

```bash
.venv/bin/python -m pytest tests/test_lab.py -v
```

### CLI

```bash
# Совместимый режим (без аргументов)
python main.py

# Калькулятор
python main.py calc 2 + 3        # → 5.0
python main.py calc 16 sqrt      # → 4.0
python main.py calc 2 ^ 10       # → 1024.0

# Meter
python main.py meter 42           # → Meter(42, unit='шт')
python main.py meter 100 --unit кг # → Meter(100, unit='кг')

# Заметки
python main.py notes demo         # демо с 3 заметками

# Asyncio
python main.py async parallel     # параллельный запуск с замером
python main.py async sequential   # последовательный (для сравнения)
python main.py async pipeline     # конвейер 5 → ×2 → +10 = 20
python main.py async prodcon      # producer-consumer
python main.py async compat       # совместимый вывод
```
