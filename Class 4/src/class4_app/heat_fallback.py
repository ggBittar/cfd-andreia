from __future__ import annotations


DEFAULT_ALPHA = 1.0


def _dirichlet_temperatures(boundary_params: dict[str, float]) -> tuple[float, float]:
    try:
        return float(boundary_params["left_temperature"]), float(boundary_params["right_temperature"])
    except KeyError as exc:
        raise ValueError("Dirichlet requer left_temperature e right_temperature.") from exc


def steady_temperature(
    x: float,
    x_min: float,
    x_max: float,
    boundary_params: dict[str, float],
) -> float:
    t_left, t_right = _dirichlet_temperatures(boundary_params)
    length = x_max - x_min
    if length <= 0.0:
        raise ValueError("O dominio deve satisfazer x_min < x_max.")
    ratio = (x - x_min) / length
    return t_left + (t_right - t_left) * ratio


def evaluate_steady_curve(
    x_values: list[float],
    x_min: float,
    x_max: float,
    boundary_params: dict[str, float],
) -> list[float]:
    return [steady_temperature(x, x_min, x_max, boundary_params) for x in x_values]


def evaluate_initial_curve(x_values: list[float], initial_temperature: float) -> list[float]:
    return [initial_temperature for _ in x_values]


def _validate_common_inputs(
    x_min: float,
    x_max: float,
    space_steps: int,
    time_steps: int,
    alpha: float,
    tf: float,
    boundary_id: str,
) -> None:
    if boundary_id != "dirichlet":
        raise ValueError(f"Condicao de contorno nao implementada: {boundary_id}")
    if x_min >= x_max:
        raise ValueError("O dominio deve satisfazer x_min < x_max.")
    if space_steps < 2:
        raise ValueError("Informe pelo menos 2 passos espaciais.")
    if time_steps <= 0:
        raise ValueError("Informe pelo menos 1 passo no tempo.")
    if alpha <= 0.0:
        raise ValueError("O parametro alpha deve ser positivo.")
    if tf < 0.0:
        raise ValueError("O tempo final deve ser nao negativo.")


def _solve_null_volume(
    x_min: float,
    x_max: float,
    space_steps: int,
    time_steps: int,
    alpha: float,
    initial_temperature: float,
    tf: float,
    t_left: float,
    t_right: float,
) -> tuple[list[float], list[list[float]], float, float]:
    dx = (x_max - x_min) / float(space_steps)
    x_values = [x_min + index * dx for index in range(space_steps + 1)]
    dt = tf / float(time_steps) if tf > 0.0 else 0.0
    fourier = alpha * dt / (dx * dx) if dt > 0.0 else 0.0
    if fourier > 0.5 + 1e-12:
        raise ValueError("Esquema explicito instavel para volume nulo: use alpha*dt/dx^2 <= 0.5.")

    current = [initial_temperature for _ in x_values]
    current[0] = t_left
    current[-1] = t_right
    history = [current[:]]

    if tf <= 0.0:
        return x_values, history, dx, 0.0

    for _ in range(time_steps):
        next_values = current[:]
        next_values[0] = t_left
        next_values[-1] = t_right
        for index in range(1, space_steps):
            west = current[index - 1]
            center = current[index]
            east = current[index + 1]
            next_values[index] = center + fourier * (east - 2.0 * center + west)
        current = next_values
        history.append(current[:])
    return x_values, history, dx, dt


def _solve_semi_volume(
    x_min: float,
    x_max: float,
    space_steps: int,
    time_steps: int,
    alpha: float,
    initial_temperature: float,
    tf: float,
    t_left: float,
    t_right: float,
) -> tuple[list[float], list[list[float]], float, float]:
    dx = (x_max - x_min) / float(space_steps)
    x_values = [x_min + 0.5 * dx + index * dx for index in range(space_steps)]
    dt = tf / float(time_steps) if tf > 0.0 else 0.0
    fourier = alpha * dt / (dx * dx) if dt > 0.0 else 0.0
    if fourier > 0.5 + 1e-12:
        raise ValueError("Esquema explicito instavel para semivolume: use alpha*dt/dx^2 <= 0.5.")

    current = evaluate_initial_curve(x_values, initial_temperature)
    history = [current[:]]

    if tf <= 0.0:
        return x_values, history, dx, 0.0

    for _ in range(time_steps):
        next_values = current[:]
        for index in range(space_steps):
            center = current[index]
            if index == 0:
                east = current[index + 1]
                next_values[index] = center + fourier * (east + 2.0 * t_left - 3.0 * center)
            elif index == space_steps - 1:
                west = current[index - 1]
                next_values[index] = center + fourier * (west + 2.0 * t_right - 3.0 * center)
            else:
                west = current[index - 1]
                east = current[index + 1]
                next_values[index] = center + fourier * (east - 2.0 * center + west)
        current = next_values
        history.append(current[:])
    return x_values, history, dx, dt


def _solve_ghost_element(
    x_min: float,
    x_max: float,
    space_steps: int,
    time_steps: int,
    alpha: float,
    initial_temperature: float,
    tf: float,
    t_left: float,
    t_right: float,
) -> tuple[list[float], list[list[float]], float, float]:
    dx = (x_max - x_min) / float(space_steps - 1)
    x_values = [x_min + index * dx for index in range(space_steps)]
    dt = tf / float(time_steps) if tf > 0.0 else 0.0
    fourier = alpha * dt / (dx * dx) if dt > 0.0 else 0.0
    if fourier > 0.5 + 1e-12:
        raise ValueError("Esquema explicito instavel para elemento fantasma: use alpha*dt/dx^2 <= 0.5.")

    current = [initial_temperature for _ in x_values]
    history = [current[:]]

    if tf <= 0.0:
        return x_values, history, dx, 0.0
    left_ghost_p = initial_temperature
    right_ghost_p = initial_temperature
    for _ in range(time_steps):
        next_values = current[:]

        left_ghost = 2.0 * t_left - current[0]
        right_ghost = 2.0 * t_right - current[-1]
        for index in range(space_steps):
            west = left_ghost_p if index == 0 else current[index - 1]
            center = current[index]
            east = right_ghost_p if index == space_steps - 1 else current[index + 1]
            next_values[index] = center + fourier * (east - 2.0 * center + west)
        current = next_values
        left_ghost_p = left_ghost
        right_ghost_p = right_ghost
        history.append(current[:])
    return x_values, history, dx, dt


def solve_heat_history_1d(
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
) -> tuple[list[float], list[float], list[list[float]], list[float], float, float, float]:
    _validate_common_inputs(x_min, x_max, space_steps, time_steps, alpha, tf, boundary_id)
    t_left, t_right = _dirichlet_temperatures(boundary_params)
    solver_map = {
        "null_volume": _solve_null_volume,
        "semi_volume": _solve_semi_volume,
        "ghost_element": _solve_ghost_element,
    }
    solver = solver_map.get(space_method_id)
    if solver is None:
        raise ValueError(f"Metodo espacial nao implementado: {space_method_id}")

    x_values, history_values, dx, dt = solver(
        x_min,
        x_max,
        space_steps,
        time_steps,
        alpha,
        initial_temperature,
        tf,
        t_left,
        t_right,
    )
    y_values = history_values[-1][:]
    steady = evaluate_steady_curve(x_values, x_min, x_max, boundary_params)
    max_error = max(abs(num - ref) for num, ref in zip(y_values, steady))
    time_values = [index * dt for index in range(len(history_values))]
    return x_values, y_values, history_values, time_values, dx, dt, max_error


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
) -> tuple[list[float], list[float], float, float, float]:
    x_values, y_values, _history_values, _time_values, dx, dt, max_error = solve_heat_history_1d(
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
    return x_values, y_values, dx, dt, max_error
