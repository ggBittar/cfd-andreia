from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpaceMethod:
    identifier: str
    label: str
    description: str
    implemented: bool


def available_space_methods() -> list[SpaceMethod]:
    return [
        SpaceMethod(
            identifier="null_volume",
            label="Volume nulo",
            description="Nos nas fronteiras com volumes degenerados em x_min e x_max, impondo Dirichlet diretamente.",
            implemented=True,
        ),
        SpaceMethod(
            identifier="semi_volume",
            label="Semivolume",
            description="Volumes de contorno com metade do tamanho de um volume interno.",
            implemented=True,
        ),
        SpaceMethod(
            identifier="ghost_element",
            label="Elemento fantasma",
            description="Volumes completos no dominio e celulas ficticias fora dele para impor os contornos.",
            implemented=True,
        ),
    ]


def find_space_method_by_id(identifier: str) -> SpaceMethod | None:
    for method in available_space_methods():
        if method.identifier == identifier:
            return method
    return None
