"""Фабрики callback_data (ограничение Telegram — 64 байта)."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCb(CallbackData, prefix="m"):
    action: str  # plate | background | wheels | interior_color | my_jobs | help | home


class NavCb(CallbackData, prefix="nav"):
    action: str  # back | cancel | confirm | redo


class OptCb(CallbackData, prefix="opt"):
    value: str


class JobCb(CallbackData, prefix="job"):
    action: str  # original | result | redo | report | other_photo | manual | operator
    job_id: int


class AdminCb(CallbackData, prefix="adm"):
    action: str  # retry
    job_id: int


class ReportCb(CallbackData, prefix="rep"):
    action: str  # skip | cancel
