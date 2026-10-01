"""Перечисления предметной области."""

from enum import StrEnum


class Role(StrEnum):
    EMPLOYEE = "employee"
    MODERATOR = "moderator"
    ADMIN = "admin"


class Operation(StrEnum):
    PLATE = "plate"
    BACKGROUND = "background"
    WHEELS = "wheels"
    INTERIOR_COLOR = "interior_color"


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class AssetType(StrEnum):
    ORIGINAL = "original"
    REFERENCE = "reference"
    RESULT = "result"


ACTIVE_JOB_STATUSES: frozenset[JobStatus] = frozenset({JobStatus.QUEUED, JobStatus.PROCESSING})

OPERATION_TITLES: dict[Operation, str] = {
    Operation.PLATE: "🔢 Замена номерной таблички",
    Operation.BACKGROUND: "🏙 Замена фона",
    Operation.WHEELS: "🛞 Замена колёсных дисков",
    Operation.INTERIOR_COLOR: "🎨 Изменение цвета салона",
}

STATUS_TITLES: dict[JobStatus, str] = {
    JobStatus.QUEUED: "🕓 В очереди",
    JobStatus.PROCESSING: "⚙️ Обрабатывается",
    JobStatus.COMPLETED: "✅ Готово",
    JobStatus.FAILED: "❌ Ошибка",
    JobStatus.NEEDS_REVIEW: "👀 Требует проверки",
}
