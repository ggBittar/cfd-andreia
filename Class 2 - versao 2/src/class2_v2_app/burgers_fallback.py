from __future__ import annotations

import math


def phi_n(x: float, t: float, n: int, c: float = 4.0, nu: float = 1.0) -> float:
    shifted_x = x - c * t - (2 * n + 1) * math.pi
    return math.exp(-(shifted_x * shifted_x) / (4.0 * nu * (t + 1.0)))


def phi_x_n(x: float, t: float, n: int, c: float = 4.0, nu: float = 1.0) -> float:
    shifted_x = x - c * t - (2 * n + 1) * math.pi
    factor = -shifted_x / (2.0 * nu * (t + 1.0))
    return factor * math.exp(-(shifted_x * shifted_x) / (4.0 * nu * (t + 1.0)))


def phi(x: float, t: float, n_limit: int, c: float = 4.0, nu: float = 1.0) -> float:
    total = 0.0
    for n in range(-n_limit, n_limit + 1):
        total += phi_n(x, t, n, c, nu)
    return total


def phi_x(x: float, t: float, n_limit: int, c: float = 4.0, nu: float = 1.0) -> float:
    total = 0.0
    for n in range(-n_limit, n_limit + 1):
        total += phi_x_n(x, t, n, c, nu)
    return total


def solution_u(x: float, t: float, n_limit: int, c: float = 4.0, nu: float = 1.0) -> float:
    phi_value = phi(x, t, n_limit, c, nu)
    if abs(phi_value) < 1e-15:
        return math.nan
    return c - 2.0 * nu * (phi_x(x, t, n_limit, c, nu) / phi_value)
