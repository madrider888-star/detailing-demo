"""Машина состояний задания: какие переходы статусов допустимы."""

from __future__ import annotations

from app.core.enums import JobStatus
from app.core.errors import InvalidStatusTransitionError

ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.QUEUED: frozenset({JobStatus.PROCESSING, JobStatus.FAILED}),
    JobStatus.PROCESSING: frozenset(
        {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.NEEDS_REVIEW}
    ),
    # Повторный запуск администратором.
    JobStatus.FAILED: frozenset({JobStatus.QUEUED}),
    JobStatus.NEEDS_REVIEW: frozenset({JobStatus.QUEUED, JobStatus.COMPLETED}),
    # Сотрудник сообщил о проблеме с готовым результатом.
    JobStatus.COMPLETED: frozenset({JobStatus.NEEDS_REVIEW}),
}

TERMINAL_STATUSES = frozenset({JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.NEEDS_REVIEW})


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def sources_for(target: JobStatus) -> frozenset[JobStatus]:
    """Все статусы, из которых можно перейти в `target`."""
    return frozenset(src for src, targets in ALLOWED_TRANSITIONS.items() if target in targets)


def ensure_transition(current: JobStatus, target: JobStatus) -> None:
    if not can_transition(current, target):
        raise InvalidStatusTransitionError(f"{current} -> {target} is not allowed")
