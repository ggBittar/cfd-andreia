# cython: language_level=3

from libc.math cimport exp, fabs, M_PI, NAN


cdef double _phi_n(double x, double t, int n, double c, double nu) noexcept:
    cdef double shifted_x = x - c * t - (2 * n + 1) * M_PI
    return exp(-(shifted_x * shifted_x) / (4.0 * nu * (t + 1.0)))


cdef double _phi_x_n(double x, double t, int n, double c, double nu) noexcept:
    cdef double shifted_x = x - c * t - (2 * n + 1) * M_PI
    cdef double factor = -shifted_x / (2.0 * nu * (t + 1.0))
    return factor * exp(-(shifted_x * shifted_x) / (4.0 * nu * (t + 1.0)))


cpdef double phi_n(double x, double t, int n, double c=4.0, double nu=1.0):
    return _phi_n(x, t, n, c, nu)


cpdef double phi_x_n(double x, double t, int n, double c=4.0, double nu=1.0):
    return _phi_x_n(x, t, n, c, nu)


cpdef double phi(double x, double t, int n_limit, double c=4.0, double nu=1.0):
    cdef int n
    cdef double total = 0.0
    for n in range(-n_limit, n_limit + 1):
        total += _phi_n(x, t, n, c, nu)
    return total


cpdef double phi_x(double x, double t, int n_limit, double c=4.0, double nu=1.0):
    cdef int n
    cdef double total = 0.0
    for n in range(-n_limit, n_limit + 1):
        total += _phi_x_n(x, t, n, c, nu)
    return total


cpdef double solution_u(double x, double t, int n_limit, double c=4.0, double nu=1.0):
    cdef double phi_value = phi(x, t, n_limit, c, nu)
    if fabs(phi_value) < 1e-15:
        return NAN
    return c - 2.0 * nu * (phi_x(x, t, n_limit, c, nu) / phi_value)
