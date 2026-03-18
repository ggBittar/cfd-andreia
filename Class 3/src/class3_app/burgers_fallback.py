from __future__ import annotations

import math


DEFAULT_C = 4.0
DEFAULT_NU = 1.0


def phi_n(x: float, t: float, n: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    shifted_x = x - c * t - (2 * n + 1) * math.pi
    return math.exp(-(shifted_x * shifted_x) / (4.0 * nu * (t + 1.0)))


def phi_x_n(x: float, t: float, n: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    shifted_x = x - c * t - (2 * n + 1) * math.pi
    factor = -shifted_x / (2.0 * nu * (t + 1.0))
    return factor * math.exp(-(shifted_x * shifted_x) / (4.0 * nu * (t + 1.0)))


def phi(x: float, t: float, n_limit: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    total = 0.0
    for n in range(-n_limit, n_limit + 1):
        total += phi_n(x, t, n, c, nu)
    return total


def phi_x(x: float, t: float, n_limit: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    total = 0.0
    for n in range(-n_limit, n_limit + 1):
        total += phi_x_n(x, t, n, c, nu)
    return total


def solution_u(x: float, t: float, n_limit: int, c: float = DEFAULT_C, nu: float = DEFAULT_NU) -> float:
    phi_value = phi(x, t, n_limit, c, nu)
    if abs(phi_value) < 1e-15:
        return math.nan
    return c - 2.0 * nu * (phi_x(x, t, n_limit, c, nu) / phi_value)


def evaluate_exact_curve(evaluator, x_values: list[float], t: float, n_value: int) -> list[float]:
    return [evaluator(x, t, n_value) for x in x_values]


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
) -> tuple[list[float], list[float], float, float]:
    if nx < 3:
        raise ValueError("Nx deve ser pelo menos 3.")
    if nt <= 0:
        raise ValueError("Nt deve ser maior que zero.")

    domain_length = x_max - x_min
    dx = domain_length / float(nx)
    dt = tf / float(nt) if tf > 0.0 else 0.0
    x_grid = [x_min + index * dx for index in range(nx)]
    current = evaluate_exact_curve(evaluator, x_grid, 0.0, n_value)

    if tf <= 0.0:
        return x_grid, current, dx, 0.0

    for _step in range(nt):
        next_values = current[:]
        for index in range(nx):
            left = current[(index - 1) % nx]
            center = current[index]
            right = current[(index + 1) % nx]

            if method_id == "ftbs":
                convection = center * (center - left) / dx
                smoothing = 0.0
            elif method_id == "ftcs":
                convection = center * (right - left) / (2.0 * dx)
                smoothing = 0.0
            elif method_id == "lax_friedrichs":
                convection = center * (right - left) / (2.0 * dx)
                smoothing = 0.5 * (left + right) - center
            else:
                raise ValueError(f"Metodo desconhecido: {method_id}")

            diffusion = nu * (right - 2.0 * center + left) / (dx * dx)
            next_values[index] = center + smoothing - dt * convection + dt * diffusion
        current = next_values

    return x_grid, current, dx, dt
