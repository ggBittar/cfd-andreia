DEFAULT_ALPHA = 1.0


def _dirichlet_temperatures(dict boundary_params):
    try:
        return float(boundary_params["left_temperature"]), float(boundary_params["right_temperature"])
    except KeyError as exc:
        raise ValueError("Dirichlet requer left_temperature e right_temperature.") from exc


def steady_temperature(double x, double x_min, double x_max, dict boundary_params):
    cdef double t_left
    cdef double t_right
    cdef double length = x_max - x_min
    cdef double ratio
    t_left, t_right = _dirichlet_temperatures(boundary_params)
    if length <= 0.0:
        raise ValueError("O dominio deve satisfazer x_min < x_max.")
    ratio = (x - x_min) / length
    return t_left + (t_right - t_left) * ratio


def evaluate_steady_curve(
    list x_values,
    double x_min,
    double x_max,
    dict boundary_params,
):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(x_values)
    cdef list values = [0.0] * count
    for i in range(count):
        values[i] = steady_temperature(x_values[i], x_min, x_max, boundary_params)
    return values


def evaluate_initial_curve(list x_values, double initial_temperature):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(x_values)
    cdef list values = [0.0] * count
    for i in range(count):
        values[i] = initial_temperature
    return values


def _validate_common_inputs(
    double x_min,
    double x_max,
    int space_steps,
    int time_steps,
    double alpha,
    double tf,
    str boundary_id,
):
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
    double x_min,
    double x_max,
    int space_steps,
    int time_steps,
    double alpha,
    double initial_temperature,
    double tf,
    double t_left,
    double t_right,
):
    cdef double dx = (x_max - x_min) / float(space_steps)
    cdef double dt = tf / float(time_steps) if tf > 0.0 else 0.0
    cdef double fourier = alpha * dt / (dx * dx) if dt > 0.0 else 0.0
    cdef int i
    cdef int step
    cdef list x_values = [0.0] * (space_steps + 1)
    cdef list current = [initial_temperature] * (space_steps + 1)
    cdef list history
    cdef list next_values

    if fourier > 0.5 + 1e-12:
        raise ValueError("Esquema explicito instavel para volume nulo: use alpha*dt/dx^2 <= 0.5.")

    for i in range(space_steps + 1):
        x_values[i] = x_min + i * dx
    current[0] = t_left
    current[space_steps] = t_right
    history = [current[:]]

    if tf <= 0.0:
        return x_values, history, dx, 0.0

    for step in range(time_steps):
        next_values = current[:]
        next_values[0] = t_left
        next_values[space_steps] = t_right
        for i in range(1, space_steps):
            next_values[i] = current[i] + fourier * (current[i + 1] - 2.0 * current[i] + current[i - 1])
        current = next_values
        history.append(current[:])
    return x_values, history, dx, dt


def _solve_semi_volume(
    double x_min,
    double x_max,
    int space_steps,
    int time_steps,
    double alpha,
    double initial_temperature,
    double tf,
    double t_left,
    double t_right,
):
    cdef double dx = (x_max - x_min) / float(space_steps)
    cdef double dt = tf / float(time_steps) if tf > 0.0 else 0.0
    cdef double fourier = alpha * dt / (dx * dx) if dt > 0.0 else 0.0
    cdef int i
    cdef int step
    cdef double center
    cdef double west
    cdef double east
    cdef list x_values = [0.0] * space_steps
    cdef list current
    cdef list history
    cdef list next_values

    if fourier > 0.5 + 1e-12:
        raise ValueError("Esquema explicito instavel para semivolume: use alpha*dt/dx^2 <= 0.5.")

    for i in range(space_steps):
        x_values[i] = x_min + 0.5 * dx + i * dx
    current = evaluate_initial_curve(x_values, initial_temperature)
    history = [current[:]]

    if tf <= 0.0:
        return x_values, history, dx, 0.0

    for step in range(time_steps):
        next_values = current[:]
        for i in range(space_steps):
            center = current[i]
            if i == 0:
                east = current[i + 1]
                next_values[i] = center + fourier * (east + 2.0 * t_left - 3.0 * center)
            elif i == space_steps - 1:
                west = current[i - 1]
                next_values[i] = center + fourier * (west + 2.0 * t_right - 3.0 * center)
            else:
                west = current[i - 1]
                east = current[i + 1]
                next_values[i] = center + fourier * (east - 2.0 * center + west)
        current = next_values
        history.append(current[:])
    return x_values, history, dx, dt


def _solve_ghost_element(
    double x_min,
    double x_max,
    int space_steps,
    int time_steps,
    double alpha,
    double initial_temperature,
    double tf,
    double t_left,
    double t_right,
):
    cdef double dx = (x_max - x_min) / float(space_steps - 1)
    cdef double dt = tf / float(time_steps) if tf > 0.0 else 0.0
    cdef double fourier = alpha * dt / (dx * dx) if dt > 0.0 else 0.0
    cdef int i
    cdef int step
    cdef double center
    cdef double west
    cdef double east
    cdef double left_ghost
    cdef double right_ghost
    cdef list x_values = [0.0] * space_steps
    cdef list current = [initial_temperature] * space_steps
    cdef list history
    cdef list next_values

    if fourier > 0.5 + 1e-12:
        raise ValueError("Esquema explicito instavel para elemento fantasma: use alpha*dt/dx^2 <= 0.5.")

    for i in range(space_steps):
        x_values[i] = x_min + i * dx
    history = [current[:]]

    if tf <= 0.0:
        return x_values, history, dx, 0.0
    left_ghost_p = initial_temperature
    right_ghost_p = initial_temperature

    for step in range(time_steps):
        next_values = current[:]
        left_ghost = 2.0 * t_left - current[0]
        right_ghost = 2.0 * t_right - current[space_steps - 1]
        for i in range(space_steps):
            center = current[i]
            west = left_ghost_p if i == 0 else current[i - 1]
            east = right_ghost_p if i == space_steps - 1 else current[i + 1]
            next_values[i] = center + fourier * (east - 2.0 * center + west)
        current = next_values
        left_ghost_p = left_ghost
        right_ghost_p = right_ghost
        history.append(current[:])
    return x_values, history, dx, dt


def solve_heat_history_1d(
    double x_min,
    double x_max,
    int space_steps,
    int time_steps,
    double alpha,
    dict boundary_params,
    double initial_temperature,
    double tf,
    str boundary_id,
    str space_method_id,
):
    cdef double t_left
    cdef double t_right
    cdef list x_values
    cdef list history_values
    cdef list time_values
    cdef list y_values
    cdef list steady_values
    cdef double dx
    cdef double dt
    cdef double max_error = 0.0
    cdef double current_error
    cdef Py_ssize_t i
    cdef object solver

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
    steady_values = evaluate_steady_curve(x_values, x_min, x_max, boundary_params)
    for i in range(len(y_values)):
        current_error = abs(y_values[i] - steady_values[i])
        if current_error > max_error:
            max_error = current_error
    time_values = [index * dt for index in range(len(history_values))]
    return x_values, y_values, history_values, time_values, dx, dt, max_error


def solve_heat_1d(
    double x_min,
    double x_max,
    int space_steps,
    int time_steps,
    double alpha,
    dict boundary_params,
    double initial_temperature,
    double tf,
    str boundary_id,
    str space_method_id,
):
    cdef list x_values
    cdef list y_values
    cdef list history_values
    cdef list time_values
    cdef double dx
    cdef double dt
    cdef double max_error

    x_values, y_values, history_values, time_values, dx, dt, max_error = solve_heat_history_1d(
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
