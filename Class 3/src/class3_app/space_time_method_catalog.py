from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpaceTimeMethod:
    identifier: str
    label: str
    description: str


def available_space_time_methods() -> list[SpaceTimeMethod]:
    return [
        SpaceTimeMethod(
            identifier="ftbs",
            label="FTBS + difusao central",
            description="Conveccao com diferenca atrasada em x e termo difusivo central.",
        ),
        SpaceTimeMethod(
            identifier="ftcs",
            label="FTCS + difusao central",
            description="Conveccao com diferenca central em x e termo difusivo central.",
        ),
        SpaceTimeMethod(
            identifier="lax_friedrichs",
            label="Lax-Friedrichs + difusao central",
            description="Media espacial estabilizante com conveccao central e difusao central.",
        ),
    ]


def find_space_time_method_by_id(identifier: str) -> SpaceTimeMethod | None:
    for method in available_space_time_methods():
        if method.identifier == identifier:
            return method
    return None
