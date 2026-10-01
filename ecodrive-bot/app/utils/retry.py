"""Повтор запросов к внешним сервисам с экспоненциальной задержкой."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.logging import get_logger
from app.services.image_editing.base import ProviderError

log = get_logger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, ProviderError) and exc.retryable


def _log_retry(state: RetryCallState) -> None:
    exc = state.outcome.exception() if state.outcome else None
    log.warning(
        "provider.retry",
        attempt=state.attempt_number,
        error=type(exc).__name__ if exc else None,
        sleep=round(state.next_action.sleep, 2) if state.next_action else None,
    )


async def call_with_retry[T](
    func: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    initial_delay: float = 2.0,
    max_delay: float = 30.0,
) -> T:
    retrying = AsyncRetrying(
        stop=stop_after_attempt(max(1, attempts)),
        wait=wait_exponential_jitter(initial=initial_delay, max=max_delay),
        retry=retry_if_exception(_is_retryable),
        before_sleep=_log_retry,
        reraise=True,
    )
    async for attempt in retrying:
        with attempt:
            return await func()
    raise AssertionError("unreachable")  # pragma: no cover
