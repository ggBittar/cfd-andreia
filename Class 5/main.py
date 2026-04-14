
x_min = 0.0
x_max = 1.0
space_steps = 10
time_steps = 100
alpha = 0.01
initial_temperature = 0.0
tf = 1.0
t_left = 100.0
t_right = 50.0

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


dx = (x_max - x_min) / float(space_steps - 1)
x_values = [x_min + index * dx for index in range(space_steps)]
print(x_values)