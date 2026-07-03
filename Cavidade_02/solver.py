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
    u_c = u[1:-1, 1:-1]

    du2_dx = (((u[1:-1, 2:] + u_c) / 2.0) ** 2 - ((u_c + u[1:-1, :-2]) / 2.0) ** 2) / dx
    duv_dy = (
        (u[2:, 1:-1] + u_c) * (v[2:, 1:-1] + v[2:, :-2])
        - (u_c + u[:-2, 1:-1]) * (v[1:-1, 1:-1] + v[1:-1, :-2])
    ) / (4.0 * dy)
    d2u_dx2 = (u[1:-1, 2:] - 2.0 * u_c + u[1:-1, :-2]) / dx**2
    d2u_dy2 = (u[2:, 1:-1] - 2.0 * u_c + u[:-2, 1:-1]) / dy**2

    u_star[1:-1, 1:-1] = u_c + dt * (-du2_dx - duv_dy + nu * (d2u_dx2 + d2u_dy2))
    return u_star

def v_estrela(u, v, dx, dy, dt, nu):
    v_star = np.copy(v)
    v_c = v[1:-1, 1:-1]

    duv_dx = (
        (u[1:-1, 2:] + u[1:-1, 1:-1]) * (v[2:, 1:-1] + v[2:, :-2])
        - (u[1:-1, 1:-1] + u[1:-1, :-2]) * (v_c + v[1:-1, :-2])
    ) / (4.0 * dx)
    dv2_dy = (((v[2:, 1:-1] + v_c) / 2.0) ** 2 - ((v_c + v[:-2, 1:-1]) / 2.0) ** 2) / dy
    d2v_dx2 = (v[1:-1, 2:] - 2.0 * v_c + v[1:-1, :-2]) / dx**2
    d2v_dy2 = (v[2:, 1:-1] - 2.0 * v_c + v[:-2, 1:-1]) / dy**2

    v_star[1:-1, 1:-1] = v_c + dt * (-duv_dx - dv2_dy + nu * (d2v_dx2 + d2v_dy2))
    return v_star


def divergencia(u, v, dx, dy):
    return (u[1:-1, 2:] - u[1:-1, 1:-1]) / dx + (v[2:, 1:-1] - v[1:-1, 1:-1]) / dy


def mascaras_red_black(shape):
    cache = getattr(mascaras_red_black, "_cache", {})
    if shape not in cache:
        jj, ii = np.indices(shape)
        red_mask = (ii + jj) % 2 == 0
        cache[shape] = (red_mask, ~red_mask)
        mascaras_red_black._cache = cache
    return cache[shape]


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


def poisson_pressao_sor(u_star, v_star, config: CavityConfig, p_inicial=None):
    if p_inicial is None:
        p_corr = np.zeros_like(u_star)
    else:
        p_corr = p_inicial.copy()

    rhs = (config.rho / config.dt) * divergencia(u_star, v_star, config.dx, config.dy)
    rhs -= rhs.mean()
    dx2 = config.dx**2
    dy2 = config.dy**2
    inv_dx2 = 1.0 / dx2
    inv_dy2 = 1.0 / dy2
    coef = 1.0 / (2.0 / dx2 + 2.0 / dy2)
    red_mask, black_mask = mascaras_red_black(rhs.shape)
    omega = config.sor_w
    um_menos_omega = 1.0 - omega
    interior = p_corr[1:-1, 1:-1]

    for iteration in range(1, config.sor_max_iter + 1):
        max_delta = 0.0
        for mask in (red_mask, black_mask):
            p_corr[:, 0] = p_corr[:, 1]
            p_corr[:, -1] = p_corr[:, -2]
            p_corr[0, :] = p_corr[1, :]
            p_corr[-1, :] = p_corr[-2, :]

            old_values = interior[mask].copy()
            gs_values = coef * (
                (p_corr[1:-1, 2:] + p_corr[1:-1, :-2]) * inv_dx2
                + (p_corr[2:, 1:-1] + p_corr[:-2, 1:-1]) * inv_dy2
                - rhs
            )
            interior[mask] = um_menos_omega * old_values + omega * gs_values[mask]
            max_delta = max(max_delta, float(np.max(np.abs(interior[mask] - old_values))))

        p_corr -= p_corr[1:-1, 1:-1].mean()

        if max_delta < config.sor_tolerance:
            return p_corr, iteration, max_delta

    return p_corr, config.sor_max_iter, max_delta


def corrigir_velocidades(u_star, v_star, p_corr, config: CavityConfig):
    u_new = np.copy(u_star)
    v_new = np.copy(v_star)
    fator_pressao = config.dt / config.rho
    u_new[1:-1, 1:-1] -= fator_pressao * (p_corr[1:-1, 1:-1] - p_corr[1:-1, :-2]) / config.dx
    v_new[1:-1, 1:-1] -= fator_pressao * (p_corr[1:-1, 1:-1] - p_corr[:-2, 1:-1]) / config.dy
    return u_new, v_new


def passo_fracionado(u, v, P, config: CavityConfig):
    boundary_conditions(u, v, P, config.u_max)
    u_star = u_estrela(u, v, config.dx, config.dy, config.dt, config.nu)
    v_star = v_estrela(u, v, config.dx, config.dy, config.dt, config.nu)
    boundary_conditions(u_star, v_star, P, config.u_max)

    u_base = u_star
    v_base = v_star
    p_base = P
    sor_iter_total = 0
    sor_error = np.inf
    div_anterior = None
    divergence_delta = np.inf

    for mass_iter in range(1, config.mass_correction_max_iter + 1):
        p_star, sor_iter, sor_error = poisson_pressao_sor(u_base, v_base, config, p_base)
        sor_iter_total += sor_iter

        u_new, v_new = corrigir_velocidades(u_base, v_base, p_star, config)
        P_new = p_star
        boundary_conditions(u_new, v_new, P_new, config.u_max)

        div = divergencia(u_new, v_new, config.dx, config.dy)
        mass_error = float(np.sqrt(np.mean(div**2)))
        mass_error_max = float(np.max(np.abs(div)))
        if div_anterior is not None:
            divergence_delta = float(np.sqrt(np.mean((div - div_anterior)**2)))

        if mass_error <= config.mass_tolerance or divergence_delta <= config.mass_tolerance:
            break

        div_anterior = div.copy()
        u_base = u_new
        v_base = v_new
        p_base = P_new
    else:
        raise FloatingPointError(
            "A convergência de massa não foi atendida dentro do passo no tempo. "
            f"mass_error={mass_error:.3e}, tolerância={config.mass_tolerance:.3e}, "
            f"divergence_delta={divergence_delta:.3e}, "
            f"correções={config.mass_correction_max_iter}, sor_iter_total={sor_iter_total}. "
            "Aumente mass_correction_max_iter, relaxe mass_tolerance, reduza CFL ou ajuste sor_w."
        )

    return u_new, v_new, P_new, {
        "sor_iter": sor_iter_total,
        "sor_error": float(sor_error),
        "mass_error": mass_error,
        "mass_error_max": mass_error_max,
        "mass_correction_iter": mass_iter,
        "divergence_delta": float(divergence_delta),
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

        if step % config.report_interval == 0 and (
            not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)) or not np.all(np.isfinite(P))
        ):
            raise FloatingPointError("A solução divergiu. Reduza CFL, Re ou sor_w em params.py.")

    return u, v, P, historico
