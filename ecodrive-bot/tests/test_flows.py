"""Переходы FSM на уровне описания сценариев (без Telegram)."""

from __future__ import annotations

from app.bot.states.flows import FLOWS, InteriorStates, StepKind, flow_for_state
from app.core.enums import Operation


def _names(op: Operation, data: dict[str, object]) -> list[str]:
    return [s.name for s in FLOWS[op].active_steps(data)]


def test_every_flow_starts_with_photo_and_ends_with_summary() -> None:
    for flow in FLOWS.values():
        assert flow.steps[0].kind is StepKind.PHOTO
        assert flow.steps[0].key == "original"
        assert flow.steps[-1].kind is StepKind.SUMMARY
        for step in flow.steps:
            assert flow.state_for(step).state == f"{flow.states.__name__}:{step.name}"


def test_plate_transitions() -> None:
    flow = FLOWS[Operation.PLATE]
    assert flow.next_step("photo", {}).name == "summary"  # type: ignore[union-attr]
    assert flow.next_step("summary", {}) is None
    assert flow.prev_step("photo", {}) is None
    assert flow.prev_step("summary", {}).name == "photo"  # type: ignore[union-attr]


def test_background_reference_step_is_conditional() -> None:
    assert _names(Operation.BACKGROUND, {"background": "city"}) == [
        "photo",
        "background",
        "summary",
    ]
    assert _names(Operation.BACKGROUND, {"background": "custom"}) == [
        "photo",
        "background",
        "reference",
        "summary",
    ]
    flow = FLOWS[Operation.BACKGROUND]
    assert flow.next_step("background", {"background": "custom"}).name == "reference"  # type: ignore[union-attr]
    assert flow.prev_step("summary", {"background": "city"}).name == "background"  # type: ignore[union-attr]


def test_effective_data_drops_inactive_steps() -> None:
    flow = FLOWS[Operation.BACKGROUND]
    data = {"original": {"file_id": "a"}, "background": "city", "reference": {"file_id": "b"}}
    effective = flow.effective_data(data)
    assert "reference" not in effective
    assert flow.image_keys(effective) == ["original"]


def test_interior_hex_step_and_position() -> None:
    flow = FLOWS[Operation.INTERIOR_COLOR]
    assert flow.position("parts", {"color": "red"}) == (3, 4)
    assert flow.position("parts", {"color": "custom"}) == (4, 5)
    assert flow.next_step("color", {"color": "custom"}).name == "hex"  # type: ignore[union-attr]
    assert flow.next_step("color", {"color": "red"}).name == "parts"  # type: ignore[union-attr]


def test_wheels_order() -> None:
    assert _names(Operation.WHEELS, {}) == ["photo", "reference", "size", "summary"]


def test_flow_for_state() -> None:
    found = flow_for_state(InteriorStates.hex.state)
    assert found is not None
    flow, step = found
    assert flow.operation is Operation.INTERIOR_COLOR and step.kind is StepKind.HEX
    assert flow_for_state(None) is None
    assert flow_for_state("ReportStates:comment") is None
    assert flow_for_state("garbage") is None
