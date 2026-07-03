import numpy as np

from params import CavityConfig


def boundary_conditions(u, v, P, u_max):
    """Aplica paredes sem escorregamento e tampa móvel usando células fantasmas."""
    # Face esquerda
    u[:, 0] = -u[:, 1]
    v[:, 0] = -v[:, 1]
    P[:, 0] = P[:, 1]

    # Face direita
    u[:, -1] = -u[:, -2]
    v[:, -1] = -v[:, -2]
    P[:, -1] = P[:, -2]

    # Face inferior
    u[0, :] = -u[1, :]
    v[0, :] = -v[1, :]
    P[0, :] = P[1, :]

    # Face superior
    u[-1, :] = 2 * u_max - u[-2,:]
    v[-1, :] = - v[-2,:]
    P[-1, :] = P[-2,:]


def u_estrela(u, v, dx, dy, dt, nu):
    u_star = np.copy(u)
    for j in range(1, u.shape[0]-1):
        for i in range(1, u.shape[1]-1):
            du2_dx = (((u[j, i+1] + u[j, i]) / 2) ** 2 - ((u[j, i] + u[j, i-1]) / 2) ** 2) / dx
            duv_dy = ((u[j+1, i] + u[j, i]) * (v[j+1, i] + v[j+1, i-1]) - (u[j, i] + u[j-1, i]) * (v[j, i] + v[j, i-1])) / (4*dy)
            d2u_dx2 = (u[j,i+1] - 2*u[j,i] + u[j,i-1]) / dx**2
            d2u_dy2 = (u[j+1,i] - 2*u[j,i] + u[j-1,i]) / dy**2
            
            u_star[j, i] = u[j, i] + dt * (-du2_dx - duv_dy + nu * (d2u_dx2 + d2u_dy2)) 
    return u_star

def v_estrela(u, v, dx, dy, dt, nu):
    v_star = np.copy(v)
    for j in range(1, v.shape[0]-1):
        for i in range(1, v.shape[1]-1):
            duv_dx = ((u[j,i+1] + u[j,i]) * (v[j+1,i] + v[j+1,i-1]) - (u[j,i] + u[j,i-1]) * (v[j,i] + v[j,i-1])) / (4*dx)
            dv2_dy = (((v[j+1, i] + v[j, i]) / 2) ** 2 - ((v[j, i] + v[j-1, i]) / 2) ** 2) / dy
            d2v_dx2 = (v[j,i+1] - 2*v[j,i] + v[j,i-1]) / dx**2
            d2v_dy2 = (v[j+1,i] - 2*v[j,i] + v[j-1,i]) / dy**2
            
            v_star[j, i] = v[j, i] + dt * (-duv_dx - dv2_dy + nu * (d2v_dx2 + d2v_dy2)) 
    return v_star


def divergencia(u, v, dx, dy):
    return (u[1:-1, 2:] - u[1:-1, 1:-1]) / dx + (v[2:, 1:-1] - v[1:-1, 1:-1]) / dy


def indice_pressao(i, j, config: CavityConfig):
    return (j - 1) * config.nx + (i - 1)


def montar_matriz_coeficientes_A(config: CavityConfig):
    """Monta a matriz A da Poisson da pressão descrita no PDF.

    A matriz representa o Laplaciano 2D nos pontos internos de pressão:
    A @ p = b, onde b = rho/dt * div(u*, v*).

    Como as condições de contorno da pressão são de gradiente normal nulo,
    a matriz é singular. A primeira linha é substituída por p[0] = 0 para
    fixar a referência de pressão.
    """
    n = config.nx * config.ny
    A = np.zeros((n, n), dtype=float)
    dx2 = config.dx**2
    dy2 = config.dy**2
    cx = 1.0 / dx2
    cy = 1.0 / dy2

    for j in range(1, config.ny + 1):
        for i in range(1, config.nx + 1):
            k = indice_pressao(i, j, config)

            if k == 0:
                A[k, k] = 1.0
                continue

            diagonal = -2.0 * (cx + cy)

            if i > 1:
                A[k, indice_pressao(i - 1, j, config)] = cx
            else:
                diagonal += cx

            if i < config.nx:
                A[k, indice_pressao(i + 1, j, config)] = cx
            else:
                diagonal += cx

            if j > 1:
                A[k, indice_pressao(i, j - 1, config)] = cy
            else:
                diagonal += cy

            if j < config.ny:
                A[k, indice_pressao(i, j + 1, config)] = cy
            else:
                diagonal += cy

            A[k, k] = diagonal

    return A


def poisson_pressao_sor(u_star, v_star, config: CavityConfig):
    p_corr = np.zeros_like(u_star)
    rhs = (config.rho / config.dt) * divergencia(u_star, v_star, config.dx, config.dy)
    rhs -= rhs.mean()
    dx2 = config.dx**2
    dy2 = config.dy**2
    coef = 1.0 / (2.0 / dx2 + 2.0 / dy2)

    for iteration in range(1, config.sor_max_iter + 1):
        max_delta = 0.0
        for j in range(1, config.ny + 1):
            for i in range(1, config.nx + 1):
                old = p_corr[j, i]
                gs_value = coef * (
                    (p_corr[j, i+1] + p_corr[j, i-1]) / dx2
                    + (p_corr[j+1, i] + p_corr[j-1, i]) / dy2
                    - rhs[j-1, i-1]
                )
                p_corr[j, i] = (1.0 - config.sor_w) * old + config.sor_w * gs_value
                max_delta = max(max_delta, abs(p_corr[j, i] - old))

        p_corr[:, 0] = p_corr[:, 1]
        p_corr[:, -1] = p_corr[:, -2]
        p_corr[0, :] = p_corr[1, :]
        p_corr[-1, :] = p_corr[-2, :]
        p_corr -= p_corr[1:-1, 1:-1].mean()

        if max_delta < config.sor_tolerance:
            return p_corr, iteration, max_delta

    return p_corr, config.sor_max_iter, max_delta


def corrigir_velocidades(u_star, v_star, p_corr, config: CavityConfig):
    u_new = np.copy(u_star)
    v_new = np.copy(v_star)
    u_new[1:-1, 1:-1] -= (config.dt / config.rho) * (p_corr[1:-1, 1:-1] - p_corr[1:-1, :-2]) / config.dx
    v_new[1:-1, 1:-1] -= (config.dt / config.rho) * (p_corr[1:-1, 1:-1] - p_corr[:-2, 1:-1]) / config.dy
    return u_new, v_new


def passo_fracionado(u, v, P, config: CavityConfig):
    boundary_conditions(u, v, P, config.u_max)
    u_star = u_estrela(u, v, config.dx, config.dy, config.dt, config.nu)
    v_star = v_estrela(u, v, config.dx, config.dy, config.dt, config.nu)
    boundary_conditions(u_star, v_star, P, config.u_max)

    p_corr, sor_iter, sor_error = poisson_pressao_sor(u_star, v_star, config)
    u_new, v_new = corrigir_velocidades(u_star, v_star, p_corr, config)
    P_new = p_corr
    boundary_conditions(u_new, v_new, P_new, config.u_max)

    div = divergencia(u_new, v_new, config.dx, config.dy)
    mass_error = float(np.sqrt(np.mean(div**2)))
    return u_new, v_new, P_new, {
        "sor_iter": sor_iter,
        "sor_error": float(sor_error),
        "mass_error": mass_error,
        "mass_error_max": float(np.max(np.abs(div))),
    }


def simular(config: CavityConfig, initial_conditions=None):
    if initial_conditions is None:
        from params import criar_condicoes_iniciais
        initial_conditions = criar_condicoes_iniciais(config)

    u = initial_conditions.u.copy()
    v = initial_conditions.v.copy()
    P = initial_conditions.P.copy()
    boundary_conditions(u, v, P, config.u_max)

    historico = []
    t = config.t_ini
    for step in range(1, config.max_steps + 1):
        if t >= config.t_final:
            break
        u_old = u.copy()
        v_old = v.copy()
        u, v, P, info = passo_fracionado(u, v, P, config)
        t += config.dt

        velocity_delta = np.sqrt(np.mean(
            (u[1:-1, 1:-1] - u_old[1:-1, 1:-1])**2
            + (v[1:-1, 1:-1] - v_old[1:-1, 1:-1])**2
        ))
        velocity_residual = velocity_delta / max(abs(config.u_max), 1.0e-12)
        mass_scale = max(abs(config.u_max) / max(config.lx, config.ly), 1.0e-12)
        mass_residual = info["mass_error"] / mass_scale
        convergence_residual = max(velocity_residual, mass_residual)

        info = {"step": step, "time": t, **info}
        info["velocity_residual"] = float(velocity_residual)
        info["mass_residual_norm"] = float(mass_residual)
        info["convergence_residual"] = float(convergence_residual)
        historico.append(info)

        if (
            config.stop_by_convergence
            and step >= config.min_steps_before_convergence
            and convergence_residual < config.convergence_tolerance
        ):
            break

        if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)) or not np.all(np.isfinite(P)):
            raise FloatingPointError("A solução divergiu. Reduza CFL, Re ou sor_w em params.py.")

    return u, v, P, historico
