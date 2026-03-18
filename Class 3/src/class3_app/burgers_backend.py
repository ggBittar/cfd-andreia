from __future__ import annotations

from dataclasses import dataclass

try:
    from . import _burgers as burgers_impl
    BACKEND_NAME = "Cython"
except ImportError:
    from . import burgers_fallback as burgers_impl
    BACKEND_NAME = "Python fallback"


DEFAULT_C = burgers_impl.DEFAULT_C
DEFAULT_NU = burgers_impl.DEFAULT_NU


@dataclass(frozen=True)
class SpaceTimeResult:
    x_values: list[float]
    y_values: list[float]
    dx: float
    dt: float


def phi_n(x: float, t: float, n: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    return burgers_impl.phi_n(x, t, n, c, nu)


def phi_x_n(x: float, t: float, n: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    return burgers_impl.phi_x_n(x, t, n, c, nu)


def phi(x: float, t: float, n_limit: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    return burgers_impl.phi(x, t, n_limit, c, nu)


def phi_x(x: float, t: float, n_limit: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    return burgers_impl.phi_x(x, t, n_limit, c, nu)


def solution_u(x: float, t: float, n_limit: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    return burgers_impl.solution_u(x, t, n_limit, c, nu)


def evaluate_exact_curve(evaluator, x_values: list[float], t: float, n_value: int) -> list[float]:
    return burgers_impl.evaluate_exact_curve(evaluator, x_values, t, n_value)


def solve_burgers_space_time(
    evaluator,
    x_min: float,
    x_max: float,
    tf: float,
    nx: int,
    nt: int,
    n_value: int,
    method_id: str,
    nu: float = DEFAULT_NU,
) -> SpaceTimeResult:
    x_values, y_values, dx, dt = burgers_impl.solve_burgers_space_time(
        evaluator,
        x_min,
        x_max,
        tf,
        nx,
        nt,
        n_value,
        method_id,
        nu,
    )
    return SpaceTimeResult(x_values=x_values, y_values=y_values, dx=dx, dt=dt)
