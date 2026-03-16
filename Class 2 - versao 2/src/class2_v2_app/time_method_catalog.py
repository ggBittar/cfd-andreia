from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


Evaluator = Callable[[float, float, int], float]


@dataclass(frozen=True)
class TimeMethod:
    identifier: str
    label: str
    description: str


def available_time_methods() -> list[TimeMethod]:
    return [
        TimeMethod(
            identifier="forward",
            label="Diferenca adiantada",
            description="Usa a derivada temporal aproximada por diferenca adiantada.",
        ),
        TimeMethod(
            identifier="backward",
            label="Diferenca atrasada",
            description="Usa a derivada temporal aproximada por diferenca atrasada.",
        ),
        TimeMethod(
            identifier="central",
            label="Diferenca central",
            description="Usa a derivada temporal aproximada por diferenca central.",
        ),
    ]


def find_time_method_by_id(identifier: str) -> TimeMethod | None:
    for method in available_time_methods():
        if method.identifier == identifier:
            return method
    return None


def evaluate_exact_curve(evaluator: Evaluator, x_values: list[float], t: float, n_value: int) -> list[float]:
    return [evaluator(x, t, n_value) for x in x_values]


def advance_curve(
    evaluator: Evaluator,
    x_values: list[float],
    tf: float,
    time_steps: int,
    n_value: int,
    method_id: str,
) -> list[float]:
    if time_steps <= 0 or tf <= 0.0:
        return evaluate_exact_curve(evaluator, x_values, 0.0, n_value)

    dt = tf / float(time_steps)
    current_values = evaluate_exact_curve(evaluator, x_values, 0.0, n_value)

    for step in range(time_steps):
        t_now = step * dt
        next_values: list[float] = []

        for index, x_value in enumerate(x_values):
            current_exact = evaluator(x_value, t_now, n_value)

            if method_id == "forward":
                next_time = min(tf, t_now + dt)
                denominator = next_time - t_now
                if denominator <= 0.0:
                    derivative = 0.0
                else:
                    derivative = (evaluator(x_value, next_time, n_value) - current_exact) / denominator
            elif method_id == "backward":
                if step == 0:
                    next_time = min(tf, t_now + dt)
                    denominator = next_time - t_now
                    if denominator <= 0.0:
                        derivative = 0.0
                    else:
                        derivative = (evaluator(x_value, next_time, n_value) - current_exact) / denominator
                else:
                    previous_time = max(0.0, t_now - dt)
                    denominator = t_now - previous_time
                    if denominator <= 0.0:
                        derivative = 0.0
                    else:
                        derivative = (current_exact - evaluator(x_value, previous_time, n_value)) / denominator
            elif method_id == "central":
                if step == 0:
                    next_time = min(tf, t_now + dt)
                    denominator = next_time - t_now
                    if denominator <= 0.0:
                        derivative = 0.0
                    else:
                        derivative = (evaluator(x_value, next_time, n_value) - current_exact) / denominator
                else:
                    previous_time = max(0.0, t_now - dt)
                    next_time = min(tf, t_now + dt)
                    denominator = next_time - previous_time
                    if denominator <= 0.0:
                        derivative = 0.0
                    else:
                        derivative = (
                            evaluator(x_value, next_time, n_value) - evaluator(x_value, previous_time, n_value)
                        ) / denominator
            else:
                raise ValueError(f"Metodo temporal desconhecido: {method_id}")

            next_values.append(current_values[index] + dt * derivative)

        current_values = next_values

    return current_values
