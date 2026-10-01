"""Серверная сборка промптов для AI-провайдера.

Промпт строится только из операции и проверенных параметров (ключи пресетов,
нормализованный HEX). Пользователь не может передать в промпт свой текст.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.enums import Operation
from app.services.operations import (
    BACKGROUND_PRESETS,
    CUSTOM,
    INTERIOR_COLORS,
    INTERIOR_PARTS,
    WHEEL_SIZES,
    normalize_hex,
)

PRESERVATION_RULES: tuple[str, ...] = (
    "This is a photo edit of a real vehicle for a car dealership listing, not a new image.",
    "Edit ONLY the region described in the task. Every other pixel must stay as in the source.",
    "Keep the exact same camera angle, framing, crop, focal length and image composition.",
)

NEGATIVE_RULES: tuple[str, ...] = (
    "Do not change the vehicle make, model, generation or trim.",
    "Do not change the body shape, proportions, panel gaps, door openings or ride height.",
    "Do not add any new parts, accessories, stickers, people, animals or objects.",
    "Do not alter headlights, tail lights, the grille, glass, mirrors or manufacturer emblems.",
    "Do not add any text, numbers, logos or watermarks.",
    "Do not change the viewing angle, perspective, crop or framing.",
    "Do not repaint the body or change its colour unless the task explicitly says so.",
    "Edit only the selected area; leave everything else untouched.",
)


@dataclass(frozen=True)
class Prompt:
    task: str
    preserve: tuple[str, ...]
    negative: tuple[str, ...]

    def render(self) -> str:
        lines = ["TASK:", self.task, "", "PRESERVE:"]
        lines += [f"- {rule}" for rule in self.preserve]
        lines += ["", "STRICTLY AVOID:"]
        lines += [f"- {rule}" for rule in self.negative]
        return "\n".join(lines)


def _background_task(params: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    key = params["background"]
    if key == CUSTOM:
        scene = (
            "the environment shown in the second (reference) image; use it only as the "
            "background scene"
        )
    else:
        scene = BACKGROUND_PRESETS[key].description
    task = (
        f"Replace only the background behind the car with {scene}. Cut the car out precisely, "
        "including antennas, mirrors and the area visible through the windows. Place it on "
        "the new ground plane at the same scale, with a natural soft contact shadow under the "
        "tyres and lighting direction consistent with the car's existing highlights."
    )
    extra = (
        "Keep the car pixel-identical: body, paint, reflections, glass, wheels, tyres, "
        "badges and number plate.",
        "Keep the real proportions and size of the car in the frame.",
    )
    return task, extra


def _wheels_task(params: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    size_hint = WHEEL_SIZES[params["size_mode"]][1]
    task = (
        "Replace only the rims (wheel discs) of every visible wheel with the rim design shown "
        "in the second (reference) image. Match each wheel's perspective, rotation and "
        f"ellipse shape; {size_hint}. Reproduce the exact spoke count and spoke shape from the "
        "reference without duplicating, merging or distorting spokes."
    )
    extra = (
        "Keep the tyres, sidewall lettering, brake discs, brake calipers and wheel arch "
        "liners unchanged.",
        "Respect partial occlusion by the wheel arches and bodywork.",
        "Keep natural shadows inside the wheel arches and on the ground.",
        "Do not change ride height, track width or suspension geometry.",
    )
    return task, extra


def _interior_task(params: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    hex_value = normalize_hex(str(params["hex"]))
    if hex_value is None:
        raise ValueError("invalid HEX in parameters")
    color_key = params["color"]
    color_name = INTERIOR_COLORS[color_key].name_en if color_key in INTERIOR_COLORS else "custom"
    parts = ", ".join(INTERIOR_PARTS[p][1] for p in params["parts"])
    task = (
        f"Recolour only these leather surfaces of the car interior: {parts}. "
        f"Target colour: {color_name} ({hex_value}). Change hue and lightness of the "
        "material only, as if it were dyed leather."
    )
    extra = (
        "Keep the leather grain texture, perforation, stitching and thread colour, seams, "
        "creases and folds.",
        "Keep the original light and shadow on every surface.",
        "Keep logos, embossing, seat belts and buckles unchanged.",
        "Keep plastic, metal, carbon, wood, glass and screens exactly as they are.",
    )
    return task, extra


def build_prompt(operation: Operation, params: dict[str, Any]) -> Prompt:
    match operation:
        case Operation.BACKGROUND:
            task, extra = _background_task(params)
        case Operation.WHEELS:
            task, extra = _wheels_task(params)
        case Operation.INTERIOR_COLOR:
            task, extra = _interior_task(params)
        case Operation.PLATE:
            task = (
                "The editable (masked) area already contains a dealer plate placed on the car — "
                "it is identical to the second (reference) image. Make it look like a real "
                "physical plate photographed in this scene: match the scene lighting, "
                "reflections, sharpness, noise and colour temperature, add a thin plastic edge "
                "and a soft contact shadow on the car behind it."
            )
            extra = (
                "Do NOT change the plate's size, position, proportions, shape, logo, lettering "
                "or colours. Do not redraw, restyle or misspell the design. Do not make it "
                "wider, narrower, taller or shorter.",
                "Keep the bumper, grille, sensors, badges and everything outside the masked "
                "area unchanged.",
            )
    return Prompt(task=task, preserve=(*PRESERVATION_RULES, *extra), negative=NEGATIVE_RULES)
