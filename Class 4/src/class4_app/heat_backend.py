from __future__ import annotations

from dataclasses import dataclass

try:
    from . import _heat as heat_impl

    if not hasattr(heat_impl, "solve_heat_history_1d"):
        raise ImportError("Extensao Cython sem a API atual.")
    BACKEND_NAME = "Cython"
except ImportError:
    from . import heat_fallback as heat_impl

    BACKEND_NAME = "Python fallback"


DEFAULT_ALPHA = heat_impl.DEFAULT_ALPHA


@dataclass(frozen=True)
class HeatResult:
    x_values: list[float]
    y_values: list[float]
    history_values: list[list[float]]
    time_values: list[float]
    dx: float
    dt: float
    max_error: float


def steady_temperature(
    x: float,
    x_min: float,
    x_max: float,
    boundary_params: dict[str, float],
) -> float:
    return heat_impl.steady_temperature(x, x_min, x_max, boundary_params)


def evaluate_steady_curve(
    x_values: list[float],
    x_min: float,
    x_max: float,
    boundary_params: dict[str, float],
) -> list[float]:
    return heat_impl.evaluate_steady_curve(x_values, x_min, x_max, boundary_params)


def evaluate_initial_curve(x_values: list[float], initial_temperature: float) -> list[float]:
    return heat_impl.evaluate_initial_curve(x_values, initial_temperature)


def solve_heat_1d(
    x_min: float,
    x_max: float,
    space_steps: int,
    time_steps: int,
    alpha: float,
    boundary_params: dict[str, float],
    initial_temperature: float,
    tf: float,
    boundary_id: str,
    space_method_id: str,
) -> HeatResult:
    x_values, y_values, history_values, time_values, dx, dt, max_error = heat_impl.solve_heat_history_1d(
        x_min,
        x_max,
        space_steps,
        time_steps,
        alpha,
        boundary_params,
        initial_temperature,
        tf,
        boundary_id,
        space_method_id,
    )
    return HeatResult(
        x_values=x_values,
        y_values=y_values,
        history_values=history_values,
        time_values=time_values,
        dx=dx,
        dt=dt,
        max_error=max_error,
    )
