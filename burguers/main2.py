import os
import numpy as np
import matplotlib.pyplot as plt
from numba import cuda

# ============================================================
# 1) PARÂMETROS DO PROBLEMA
# ============================================================
# Domínio periódico: x em [0, 2*pi)
x0 = 0.0
xL = 2.0 * np.pi

# Parâmetros da solução analítica
c = 1.0          # velocidade de advecção
nu = 0.07        # viscosidade cinemática
t_final = 1.0    # tempo final para comparação

# Refinamentos de malha
refinamentos = [64, 128, 256, 512]

# Quantos termos usar na soma truncada da solução analítica
n_terms = 80

# Parâmetros de estabilidade do esquema explícito
CFL = 0.20
FOURIER = 0.20

# Pasta para salvar os gráficos
os.makedirs("graficos", exist_ok=True)


# ============================================================
# 2) SOLUÇÃO ANALÍTICA
# ============================================================
def burgers_analitica(x, t, c, nu, n_terms=80):
    """
    Solução analítica periódica da equação de Burgers viscosa.

    Fórmula usada:
      u(x,t) = c - 2*nu * phi_x(z, tau)/phi(z, tau)
    onde
      z = x - c*t
      tau = t + 1

    e
      phi(z, tau) = sum exp( -(z - (2n+1)pi)^2 / (4 nu tau) )

    A derivada phi_x é calculada analiticamente.
    """
    z = x - c * t
    tau = t + 1.0

    phi = np.zeros_like(x, dtype=np.float64)
    dphi = np.zeros_like(x, dtype=np.float64)

    for n in range(-n_terms, n_terms + 1):
        a = z - (2 * n + 1) * np.pi
        expo = np.exp(-(a * a) / (4.0 * nu * tau))
        phi += expo
        dphi += -(a / (2.0 * nu * tau)) * expo

    u = c - 2.0 * nu * (dphi / phi)
    return u


# ============================================================
# 3) KERNEL CUDA - ESQUEMA UPWIND
# ============================================================
@cuda.jit
def kernel_burgers_upwind(u_old, u_new, dx, dt, nu):
    """
    Atualiza um passo de tempo da equação de Burgers 1D viscosa.

    Esquema explícito:
      u^{n+1}_i = u^n_i - dt * u_i * dudx + dt * nu * d2udx2

    Termo convectivo:
      dudx por UPWIND

    Condição de contorno:
      periódica
    """
    i = cuda.grid(1)
    n = u_old.size

    if i < n:
        # índices periódicos
        im1 = i - 1
        if im1 < 0:
            im1 = n - 1

        ip1 = i + 1
        if ip1 >= n:
            ip1 = 0

        ui = u_old[i]

        # ---------------------------------------------
        # Termo convectivo com upwind
        # Se ui > 0, usa derivada para trás
        # Se ui < 0, usa derivada para frente
        # ---------------------------------------------
        if ui >= 0.0:
            dudx = (ui - u_old[im1]) / dx
        else:
            dudx = (u_old[ip1] - ui) / dx

        # ---------------------------------------------
        # Termo difusivo com diferença central
        # ---------------------------------------------
        d2udx2 = (u_old[ip1] - 2.0 * ui + u_old[im1]) / (dx * dx)

        # ---------------------------------------------
        # Atualização explícita
        # ---------------------------------------------
        u_new[i] = ui - dt * ui * dudx + dt * nu * d2udx2


# ============================================================
# 4) KERNEL CUDA - ESQUEMA CENTRAL
# ============================================================
@cuda.jit
def kernel_burgers_central(u_old, u_new, dx, dt, nu):
    """
    Atualiza um passo de tempo da equação de Burgers 1D viscosa.

    Termo convectivo:
      dudx por diferença central

    Termo difusivo:
      diferença central

    Condição de contorno:
      periódica
    """
    i = cuda.grid(1)
    n = u_old.size

    if i < n:
        # índices periódicos
        im1 = i - 1
        if im1 < 0:
            im1 = n - 1

        ip1 = i + 1
        if ip1 >= n:
            ip1 = 0

        ui = u_old[i]

        # ---------------------------------------------
        # Termo convectivo com diferença central
        # ---------------------------------------------
        dudx = (u_old[ip1] - u_old[im1]) / (2.0 * dx)

        # ---------------------------------------------
        # Termo difusivo com diferença central
        # ---------------------------------------------
        d2udx2 = (u_old[ip1] - 2.0 * ui + u_old[im1]) / (dx * dx)

        # ---------------------------------------------
        # Atualização explícita
        # ---------------------------------------------
        u_new[i] = ui - dt * ui * dudx + dt * nu * d2udx2


# ============================================================
# 5) FUNÇÃO DE ERRO
# ============================================================
def erro_l2_rel(u_num, u_ex):
    """
    Erro L2 relativo:
      ||u_num - u_ex||_2 / ||u_ex||_2
    """
    num = np.sqrt(np.sum((u_num - u_ex) ** 2))
    den = np.sqrt(np.sum(u_ex ** 2))
    return num / den


def erro_linf_rel(u_num, u_ex):
    """
    Erro infinito relativo:
      max|u_num-u_ex| / max|u_ex|
    """
    num = np.max(np.abs(u_num - u_ex))
    den = np.max(np.abs(u_ex))
    return num / den


# ============================================================
# 6) SIMULAÇÃO CUDA PARA UMA MALHA E UM ESQUEMA
# ============================================================
def simular_burgers_cuda(Nx, esquema, c, nu, t_final, n_terms=80):
    """
    Roda a simulação da equação de Burgers 1D na GPU.

    Entradas:
      Nx       -> número de pontos da malha
      esquema  -> "upwind" ou "central"

    Saídas:
      x        -> malha
      u_num    -> solução numérica em t_final
      u_ex     -> solução analítica em t_final
      dx, dt, nt
    """
    # ---------------------------------------------
    # Malha periódica: endpoint=False evita repetir
    # o ponto x = 2*pi, já que ele é igual ao x = 0
    # ---------------------------------------------
    x = np.linspace(x0, xL, Nx, endpoint=False, dtype=np.float64)
    dx = (xL - x0) / Nx

    # ---------------------------------------------
    # Condição inicial: usa a própria solução analítica
    # em t = 0
    # ---------------------------------------------
    u0 = burgers_analitica(x, 0.0, c, nu, n_terms=n_terms)

    # ---------------------------------------------
    # Escolha do dt para o método explícito
    # restrição advectiva + difusiva
    # ---------------------------------------------
    umax0 = max(np.max(np.abs(u0)), 1e-12)

    dt_adv = CFL * dx / umax0
    dt_dif = FOURIER * dx * dx / nu
    dt = min(dt_adv, dt_dif)

    # ajusta dt para bater exatamente em t_final
    nt = int(np.ceil(t_final / dt))
    dt = t_final / nt

    # ---------------------------------------------
    # Vetores na GPU
    # ---------------------------------------------
    u_old_d = cuda.to_device(u0)
    u_new_d = cuda.device_array_like(u_old_d)

    # configuração CUDA
    threads_per_block = 128
    blocks_per_grid = (Nx + threads_per_block - 1) // threads_per_block

    # ---------------------------------------------
    # Marcha no tempo
    # ---------------------------------------------
    for _ in range(nt):
        if esquema == "upwind":
            kernel_burgers_upwind[blocks_per_grid, threads_per_block](
                u_old_d, u_new_d, dx, dt, nu
            )
        elif esquema == "central":
            kernel_burgers_central[blocks_per_grid, threads_per_block](
                u_old_d, u_new_d, dx, dt, nu
            )
        else:
            raise ValueError("Esquema inválido. Use 'upwind' ou 'central'.")

        # troca os ponteiros: o novo vira velho
        u_old_d, u_new_d = u_new_d, u_old_d

    # traz resultado da GPU para CPU
    u_num = u_old_d.copy_to_host()

    # solução analítica no tempo final
    u_ex = burgers_analitica(x, t_final, c, nu, n_terms=n_terms)

    return x, u_num, u_ex, dx, dt, nt


# ============================================================
# 7) LOOP NOS REFINAMENTOS E NOS ESQUEMAS
# ============================================================
if not cuda.is_available():
    raise RuntimeError(
        "CUDA não está disponível. Verifique driver, toolkit e Numba."
    )

resultados = {
    "upwind": {"Nx": [], "dx": [], "L2": [], "Linf": [], "x": None, "u": None, "uex": None},
    "central": {"Nx": [], "dx": [], "L2": [], "Linf": [], "x": None, "u": None, "uex": None},
}

for esquema in ["upwind", "central"]:
    print(f"\n=== Esquema: {esquema} ===")

    for Nx in refinamentos:
        x, u_num, u_ex, dx, dt, nt = simular_burgers_cuda(
            Nx=Nx,
            esquema=esquema,
            c=c,
            nu=nu,
            t_final=t_final,
            n_terms=n_terms
        )

        eL2 = erro_l2_rel(u_num, u_ex)
        eLinf = erro_linf_rel(u_num, u_ex)

        resultados[esquema]["Nx"].append(Nx)
        resultados[esquema]["dx"].append(dx)
        resultados[esquema]["L2"].append(eL2)
        resultados[esquema]["Linf"].append(eLinf)

        # guarda a solução da malha mais fina para plot
        if Nx == refinamentos[-1]:
            resultados[esquema]["x"] = x.copy()
            resultados[esquema]["u"] = u_num.copy()
            resultados[esquema]["uex"] = u_ex.copy()

        print(
            f"Nx = {Nx:4d} | dx = {dx:.6e} | dt = {dt:.6e} | nt = {nt:6d} "
            f"| L2 = {eL2:.6e} | Linf = {eLinf:.6e}"
        )


# ============================================================
# 8) ORDEM OBSERVADA DE CONVERGÊNCIA
# ============================================================
def ordem_observada(erros, hs):
    """
    Calcula ordens observadas:
      p_i = log(e_i/e_{i+1}) / log(h_i/h_{i+1})
    """
    ordens = []
    for i in range(len(erros) - 1):
        p = np.log(erros[i] / erros[i + 1]) / np.log(hs[i] / hs[i + 1])
        ordens.append(p)
    return ordens

for esquema in ["upwind", "central"]:
    erros = np.array(resultados[esquema]["L2"])
    hs = np.array(resultados[esquema]["dx"])
    p_obs = ordem_observada(erros, hs)

    print(f"\nOrdem observada em L2 para {esquema}:")
    for i in range(len(p_obs)):
        print(
            f"de Nx={refinamentos[i]} para Nx={refinamentos[i+1]} -> p = {p_obs[i]:.4f}"
        )


# ============================================================
# 9) GRÁFICO 1 - PERFIL NA MALHA MAIS FINA
# ============================================================
plt.figure(figsize=(10, 6))

# solução analítica
x_fino = resultados["upwind"]["x"]
u_ex_fino = resultados["upwind"]["uex"]
plt.plot(x_fino, u_ex_fino, "k-", linewidth=3, label="Analítica")

# numéricas
plt.plot(
    resultados["upwind"]["x"],
    resultados["upwind"]["u"],
    "--",
    linewidth=2,
    label="Numérica CUDA - Upwind"
)

plt.plot(
    resultados["central"]["x"],
    resultados["central"]["u"],
    "-.",
    linewidth=2,
    label="Numérica CUDA - Central"
)

plt.xlabel("x")
plt.ylabel("u(x, t_final)")
plt.title(f"Equação de Burgers viscosa em t = {t_final}")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("graficos/burgers_perfil_malha_fina.png", dpi=300, bbox_inches="tight")
plt.close()


# ============================================================
# 10) GRÁFICO 2 - CONVERGÊNCIA L2
# ============================================================
plt.figure(figsize=(10, 6))

plt.loglog(
    resultados["upwind"]["dx"],
    resultados["upwind"]["L2"],
    "o-",
    linewidth=2,
    markersize=7,
    label="Upwind"
)

plt.loglog(
    resultados["central"]["dx"],
    resultados["central"]["L2"],
    "s-",
    linewidth=2,
    markersize=7,
    label="Diferença central"
)

plt.xlabel("dx")
plt.ylabel("Erro L2 relativo")
plt.title("Convergência da solução numérica vs solução analítica")
plt.grid(True, which="both")
plt.legend()
plt.tight_layout()
plt.savefig("graficos/burgers_convergencia_L2.png", dpi=300, bbox_inches="tight")
plt.close()


# ============================================================
# 11) GRÁFICO 3 - CONVERGÊNCIA LINF
# ============================================================
plt.figure(figsize=(10, 6))

plt.loglog(
    resultados["upwind"]["dx"],
    resultados["upwind"]["Linf"],
    "o-",
    linewidth=2,
    markersize=7,
    label="Upwind"
)

plt.loglog(
    resultados["central"]["dx"],
    resultados["central"]["Linf"],
    "s-",
    linewidth=2,
    markersize=7,
    label="Diferença central"
)

plt.xlabel("dx")
plt.ylabel("Erro Linf relativo")
plt.title("Convergência em norma infinita")
plt.grid(True, which="both")
plt.legend()
plt.tight_layout()
plt.savefig("graficos/burgers_convergencia_Linf.png", dpi=300, bbox_inches="tight")
plt.close()


# ============================================================
# 12) TABELA FINAL NO TERMINAL
# ============================================================
print("\nResumo final:")
for esquema in ["upwind", "central"]:
    print(f"\nEsquema: {esquema}")
    print(" Nx        dx              L2_rel           Linf_rel")
    for Nx, dx, eL2, eLinf in zip(
        resultados[esquema]["Nx"],
        resultados[esquema]["dx"],
        resultados[esquema]["L2"],
        resultados[esquema]["Linf"]
    ):
        print(f"{Nx:4d}   {dx: .6e}   {eL2: .6e}   {eLinf: .6e}")

print("\nGráficos salvos na pasta 'graficos'.")