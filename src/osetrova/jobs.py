"""Асинхронные задачи: параллелизм, конвейер, producer-consumer.

Демонстрирует реальные сценарии asyncio: gather, wait_for,
asyncio.Queue и async-конвейер.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Sequence


# ---------------------------------------------------------------------------
# Симуляция сетевого запроса
# ---------------------------------------------------------------------------

async def fetch_sim(url: str, delay: float = 0.1) -> dict[str, Any]:
    """Имитирует HTTP-запрос: ждёт *delay* секунд, возвращает dict.

    В реальном коде здесь был бы ``aiohttp.get(url)``.
    """
    await asyncio.sleep(delay)
    return {"url": url, "status": 200, "elapsed": delay}


# ---------------------------------------------------------------------------
# Параллельный / последовательный запуск
# ---------------------------------------------------------------------------

async def run_parallel(tasks: list[tuple[str, float]]) -> list[dict[str, Any]]:
    """Запускает *tasks* параллельно через :func:`asyncio.gather`.

    Каждый элемент — ``(url, delay)``.
    """
    coros = [fetch_sim(url, delay) for url, delay in tasks]
    results = await asyncio.gather(*coros)
    return list(results)


async def run_sequential(tasks: list[tuple[str, float]]) -> list[dict[str, Any]]:
    """Запускает *tasks* последовательно (для сравнения со параллельным)."""
    results: list[dict[str, Any]] = []
    for url, delay in tasks:
        results.append(await fetch_sim(url, delay))
    return results


# ---------------------------------------------------------------------------
# Таймаут
# ---------------------------------------------------------------------------

async def run_with_timeout(
    coro: Awaitable[Any],
    seconds: float,
) -> Any | None:
    """Оборачивает корутину в :func:`asyncio.wait_for`.

    Возвращает результат или ``None`` при таймауте.
    """
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        return None


# ---------------------------------------------------------------------------
# Конвейер (pipeline)
# ---------------------------------------------------------------------------

async def run_pipeline(
    data: Any,
    *stages: Callable[..., Awaitable[Any]],
) -> Any:
    """Прогоняет *data* через цепочку async-функций последовательно.

    Результат каждого шага передаётся на вход следующему.
    """
    result = data
    for stage in stages:
        result = await stage(result)
    return result


# ---------------------------------------------------------------------------
# Producer-consumer
# ---------------------------------------------------------------------------

async def producer_consumer(
    items: Sequence[Any],
    workers: int = 2,
) -> list[Any]:
    """Классический паттерн: один producer, несколько consumer через Queue.

    Каждый consumer «обрабатывает» элемент (удваивает число или
    добавляет суффикс к строке) и кладёт результат в список.
    """
    queue: asyncio.Queue[Any | None] = asyncio.Queue()
    results: list[Any] = []
    lock = asyncio.Lock()

    async def consumer(name: int) -> None:
        while True:
            item = await queue.get()
            if item is None:
                queue.task_done()
                break
            await asyncio.sleep(0)  # имитация работы
            processed = item * 2 if isinstance(item, (int, float)) else f"{item}_done"
            async with lock:
                results.append(processed)
            queue.task_done()

    async def producer() -> None:
        for item in items:
            await queue.put(item)
        for _ in range(workers):
            await queue.put(None)  # сигнал остановки

    consumers = [asyncio.create_task(consumer(i)) for i in range(workers)]
    await producer()
    await asyncio.gather(*consumers)
    return results


# ---------------------------------------------------------------------------
# Совместимость с оригинальным API
# ---------------------------------------------------------------------------

async def _double(number: int) -> int:
    """Удваивает число (оставлена для обратной совместимости)."""
    await asyncio.sleep(0)
    return number * 2


async def run_two(x: int, y: int) -> list[int]:
    """Запускает две задачи _double параллельно."""
    left, right = await asyncio.gather(_double(x), _double(y))
    return [left, right]
