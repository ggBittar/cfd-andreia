from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BoundaryParameter:
    key: str
    label: str
    default_value: str
    description: str


@dataclass(frozen=True)
class BoundaryConditionMethod:
    identifier: str
    label: str
    description: str
    implemented: bool
    parameters: list[BoundaryParameter] = field(default_factory=list)


def available_boundary_conditions() -> list[BoundaryConditionMethod]:
    return [
        BoundaryConditionMethod(
            identifier="dirichlet",
            label="Dirichlet",
            description="Temperatura prescrita nas fronteiras esquerda e direita.",
            implemented=True,
            parameters=[
                BoundaryParameter(
                    key="left_temperature",
                    label="Temperatura esquerda",
                    default_value="100.0",
                    description="Valor de temperatura imposto em x_min.",
                ),
                BoundaryParameter(
                    key="right_temperature",
                    label="Temperatura direita",
                    default_value="500.0",
                    description="Valor de temperatura imposto em x_max.",
                ),
            ],
        ),
        BoundaryConditionMethod(
            identifier="neumann",
            label="Neumann",
            description="Fluxo de calor prescrito nas fronteiras.",
            implemented=False,
            parameters=[
                BoundaryParameter(
                    key="left_flux",
                    label="Fluxo esquerdo",
                    default_value="0.0",
                    description="Fluxo imposto em x_min.",
                ),
                BoundaryParameter(
                    key="right_flux",
                    label="Fluxo direito",
                    default_value="0.0",
                    description="Fluxo imposto em x_max.",
                ),
            ],
        ),
        BoundaryConditionMethod(
            identifier="robin",
            label="Robin",
            description="Combinacao entre temperatura e fluxo na fronteira.",
            implemented=False,
            parameters=[
                BoundaryParameter(
                    key="left_h",
                    label="h esquerdo",
                    default_value="10.0",
                    description="Coeficiente convectivo em x_min.",
                ),
                BoundaryParameter(
                    key="left_environment",
                    label="T_inf esquerda",
                    default_value="25.0",
                    description="Temperatura do meio externo em x_min.",
                ),
                BoundaryParameter(
                    key="right_h",
                    label="h direito",
                    default_value="10.0",
                    description="Coeficiente convectivo em x_max.",
                ),
                BoundaryParameter(
                    key="right_environment",
                    label="T_inf direita",
                    default_value="25.0",
                    description="Temperatura do meio externo em x_max.",
                ),
            ],
        ),
    ]


def find_boundary_condition_by_id(identifier: str) -> BoundaryConditionMethod | None:
    for method in available_boundary_conditions():
        if method.identifier == identifier:
            return method
    return None
