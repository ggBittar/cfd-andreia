# cython: language_level=3

from libc.math cimport M_PI, NAN, exp, fabs


DEFAULT_C = 4.0
DEFAULT_NU = 1.0


cdef double _phi_n(double x, double t, int n, double c, double nu) noexcept:
    cdef double shifted_x = x - c * t - (2 * n + 1) * M_PI
    return exp(-(shifted_x * shifted_x) / (4.0 * nu * (t + 1.0)))


cdef double _phi_x_n(double x, double t, int n, double c, double nu) noexcept:
    cdef double shifted_x = x - c * t - (2 * n + 1) * M_PI
    cdef double factor = -shifted_x / (2.0 * nu * (t + 1.0))
    return factor * exp(-(shifted_x * shifted_x) / (4.0 * nu * (t + 1.0)))


cpdef double phi_n(double x, double t, int n, double c=DEFAULT_C, double nu=DEFAULT_NU):
    return _phi_n(x, t, n, c, nu)


cpdef double phi_x_n(double x, double t, int n, double c=DEFAULT_C, double nu=DEFAULT_NU):
    return _phi_x_n(x, t, n, c, nu)


cpdef double phi(double x, double t, int n_limit, double c=DEFAULT_C, double nu=DEFAULT_NU):
    cdef int n
    cdef double total = 0.0
    for n in range(-n_limit, n_limit + 1):
        total += _phi_n(x, t, n, c, nu)
    return total


cpdef double phi_x(double x, double t, int n_limit, double c=DEFAULT_C, double nu=DEFAULT_NU):
    cdef int n
    cdef double total = 0.0
    for n in range(-n_limit, n_limit + 1):
        total += _phi_x_n(x, t, n, c, nu)
    return total


cpdef double solution_u(double x, double t, int n_limit, double c=DEFAULT_C, double nu=DEFAULT_NU):
    cdef double phi_value = phi(x, t, n_limit, c, nu)
    if fabs(phi_value) < 1e-15:
        return NAN
    return c - 2.0 * nu * (phi_x(x, t, n_limit, c, nu) / phi_value)


cpdef list evaluate_exact_curve(object evaluator, list x_values, double t, int n_value):
    cdef Py_ssize_t index
    cdef Py_ssize_t total = len(x_values)
    cdef list result = [0.0] * total

    for index in range(total):
        result[index] = evaluator(x_values[index], t, n_value)
    return result


cpdef tuple solve_burgers_space_time(
    object evaluator,
    double x_min,
    double x_max,
    double tf,
    int nx,
    int nt,
    int n_value,
    str method_id,
    double nu=DEFAULT_NU,
):
    cdef double domain_length
    cdef double dx
    cdef double dt
    cdef int step
    cdef int index
    cdef int method_kind
    cdef double left
    cdef double center
    cdef double right
    cdef double convection
    cdef double smoothing
    cdef double diffusion
    cdef list x_grid
    cdef list current
    cdef list next_values

    if nx < 3:
        raise ValueError("Nx deve ser pelo menos 3.")
    if nt <= 0:
        raise ValueError("Nt deve ser maior que zero.")

    if method_id == "ftbs":
        method_kind = 0
    elif method_id == "ftcs":
        method_kind = 1
    elif method_id == "lax_friedrichs":
        method_kind = 2
    else:
        raise ValueError(f"Metodo desconhecido: {method_id}")

    domain_length = x_max - x_min
    dx = domain_length / nx
    dt = tf / nt if tf > 0.0 else 0.0
    x_grid = [x_min + index * dx for index in range(nx)]
    current = evaluate_exact_curve(evaluator, x_grid, 0.0, n_value)

    if tf <= 0.0:
        return x_grid, current, dx, 0.0

    for step in range(nt):
        next_values = current[:]
        for index in range(nx):
            left = current[(index - 1) % nx]
            center = current[index]
            right = current[(index + 1) % nx]

            if method_kind == 0:
                convection = center * (center - left) / dx
                smoothing = 0.0
            elif method_kind == 1:
                convection = center * (right - left) / (2.0 * dx)
                smoothing = 0.0
            else:
                convection = center * (right - left) / (2.0 * dx)
                smoothing = 0.5 * (left + right) - center

            diffusion = nu * (right - 2.0 * center + left) / (dx * dx)
            next_values[index] = center + smoothing - dt * convection + dt * diffusion
        current = next_values

    return x_grid, current, dx, dt
