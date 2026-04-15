import os
import csv
import time
import math
import numpy as np
import matplotlib.pyplot as plt
import cupy as cp

# ============================================================
# Equação de Burgers 1D viscosa
#
#   du/dt + u du/dx = nu d²u/dx²
#
# Implementações:
# - GPU com CuPy
# - CPU com NumPy (comparação apenas em malha grosseira)
#
# Esquemas convectivos testados:
# - Upwind
# - Diferença central
#
# O código:
# - compara com a solução analítica
# - testa um vetor de refinamentos de malha
# - salva gráficos em uma pasta
# - salva CSV com erros e tempos
# - calcula ordens observadas
# ============================================================

# ------------------------------
# Configurações gerais do problema
# ------------------------------
X0 = 0.0
XL = 2.0 * np.pi
C = 1.0
NU = 0.07
T_FINAL = 1.0

# Refinamentos para o estudo de convergência GPU
REFINAMENTOS = [32, 64, 128, 256, 512, 1024, 2048, 4096]

# Malha grosseira usada na comparação CPU x GPU
NX_CPU_COMPARACAO = 1024

# Truncamento da série da solução analítica
N_TERMS = 80

# Restrições de estabilidade para o método explícito
CFL = 0.20
FOURIER = 0.20

# Diretórios de saída
PASTA_GRAFICOS = "graficos"
PASTA_DADOS = "dados"
os.makedirs(PASTA_GRAFICOS, exist_ok=True)
os.makedirs(PASTA_DADOS, exist_ok=True)


# ============================================================
# 1) SOLUÇÃO ANALÍTICA
# ============================================================
def burgers_analitica(x, t, c=C, nu=NU, n_terms=N_TERMS):
    """
    Solução analítica periódica da equação de Burgers viscosa.

    Fórmulas:
      u(x,t) = c - 2*nu * phi_x(z, tau) / phi(z, tau)
      z = x - c t
      tau = t + 1

      phi(z, tau) = sum_{n=-N}^{N} exp(-(z-(2n+1)pi)^2 / (4 nu tau))

    A série infinita é truncada em [-n_terms, n_terms].
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

    return c - 2.0 * nu * (dphi / phi)


# ============================================================
# 2) MÉTRICAS DE ERRO
# ============================================================
def erro_l2_rel(u_num, u_ex):
    num = np.sqrt(np.sum((u_num - u_ex) ** 2))
    den = np.sqrt(np.sum(u_ex ** 2))
    return num / den


def erro_linf_rel(u_num, u_ex):
    num = np.max(np.abs(u_num - u_ex))
    den = np.max(np.abs(u_ex))
    return num / den


def ordem_observada(erros, hs):
    ordens = []
    for i in range(len(erros) - 1):
        p = np.log(erros[i] / erros[i + 1]) / np.log(hs[i] / hs[i + 1])
        ordens.append(p)
    return ordens


# ============================================================
# 3) ESCOLHA DO PASSO DE TEMPO
# ============================================================
def calcular_dt_explicito(u0, dx, nu=NU, t_final=T_FINAL, cfl=CFL, fourier=FOURIER):
    """
    Escolhe dt com base nas restrições advectiva e difusiva.
    Em seguida ajusta dt para que nt * dt = t_final exatamente.
    """
    umax0 = max(np.max(np.abs(u0)), 1e-12)
    dt_adv = cfl * dx / umax0
    dt_dif = fourier * dx * dx / nu
    dt = min(dt_adv, dt_dif)
    nt = int(np.ceil(t_final / dt))
    dt = t_final / nt
    return dt, nt


# ============================================================
# 4) PASSOS NUMÉRICOS EM CPU (NumPy)
# ============================================================
def passo_cpu_upwind(u_old, dx, dt, nu=NU):
    """
    Passo explícito em CPU com upwind no termo convectivo.
    Contorno periódico via np.roll.
    """
    u_im1 = np.roll(u_old, 1)
    u_ip1 = np.roll(u_old, -1)

    dudx = np.where(
        u_old >= 0.0,
        (u_old - u_im1) / dx,
        (u_ip1 - u_old) / dx,
    )

    d2udx2 = (u_ip1 - 2.0 * u_old + u_im1) / (dx * dx)
    return u_old - dt * u_old * dudx + dt * nu * d2udx2


def passo_cpu_central(u_old, dx, dt, nu=NU):
    """
    Passo explícito em CPU com diferença central no termo convectivo.
    """
    u_im1 = np.roll(u_old, 1)
    u_ip1 = np.roll(u_old, -1)

    dudx = (u_ip1 - u_im1) / (2.0 * dx)
    d2udx2 = (u_ip1 - 2.0 * u_old + u_im1) / (dx * dx)
    return u_old - dt * u_old * dudx + dt * nu * d2udx2


# ============================================================
# 5) PASSOS NUMÉRICOS EM GPU (CuPy)
# ============================================================
# Os kernels abaixo fundem o stencil completo em um único launch,
# evitando vários kernels pequenos gerados por cp.roll/cp.where
# a cada passo de tempo.
KERNEL_UPWIND = cp.ElementwiseKernel(
    "raw float64 u_old, float64 dx, float64 dt, float64 nu, int32 n",
    "float64 u_new",
    r"""
    const int im1 = (i == 0) ? (n - 1) : (i - 1);
    const int ip1 = (i == n - 1) ? 0 : (i + 1);

    const double ui = u_old[i];
    const double uim1 = u_old[im1];
    const double uip1 = u_old[ip1];

    double dudx;
    if (ui >= 0.0) {
        dudx = (ui - uim1) / dx;
    } else {
        dudx = (uip1 - ui) / dx;
    }

    const double d2udx2 = (uip1 - 2.0 * ui + uim1) / (dx * dx);
    u_new = ui - dt * ui * dudx + dt * nu * d2udx2;
    """,
    "burgers_upwind_kernel",
)


KERNEL_CENTRAL = cp.ElementwiseKernel(
    "raw float64 u_old, float64 dx, float64 dt, float64 nu, int32 n",
    "float64 u_new",
    r"""
    const int im1 = (i == 0) ? (n - 1) : (i - 1);
    const int ip1 = (i == n - 1) ? 0 : (i + 1);

    const double ui = u_old[i];
    const double uim1 = u_old[im1];
    const double uip1 = u_old[ip1];

    const double dudx = (uip1 - uim1) / (2.0 * dx);
    const double d2udx2 = (uip1 - 2.0 * ui + uim1) / (dx * dx);
    u_new = ui - dt * ui * dudx + dt * nu * d2udx2;
    """,
    "burgers_central_kernel",
)


def passo_gpu_upwind(u_old, u_new, dx, dt, nu=NU):
    KERNEL_UPWIND(u_old, dx, dt, nu, np.int32(u_old.size), u_new)


def passo_gpu_central(u_old, u_new, dx, dt, nu=NU):
    KERNEL_CENTRAL(u_old, dx, dt, nu, np.int32(u_old.size), u_new)


# ============================================================
# 6) SIMULAÇÃO GPU COM CUPY
# ============================================================
def simular_gpu(Nx, esquema, salvar_snapshots=False):
    x = np.linspace(X0, XL, Nx, endpoint=False, dtype=np.float64)
    dx = (XL - X0) / Nx
    u0 = burgers_analitica(x, 0.0)
    dt, nt = calcular_dt_explicito(u0, dx)

    # solução inicial enviada para a GPU
    u0_gpu = cp.asarray(u0)
    u1_gpu = cp.empty_like(u0_gpu)

    # snapshots em tempos específicos
    snapshots = {}
    tempos_snap = [0.0, 0.25 * T_FINAL, 0.50 * T_FINAL, 0.75 * T_FINAL, T_FINAL]
    if salvar_snapshots:
        snapshots[0.0] = u0.copy()

    # warm-up para carregar contexto CUDA e evitar medir inicialização
    if esquema == "upwind":
        passo_gpu_upwind(u0_gpu, u1_gpu, dx, dt, NU)
    else:
        passo_gpu_central(u0_gpu, u1_gpu, dx, dt, NU)
    cp.cuda.Stream.null.synchronize()

    # reinicializa para a simulação medida
    u_gpu = cp.asarray(u0)
    u_gpu_new = cp.empty_like(u_gpu)

    t0 = time.perf_counter()
    for n in range(nt):
        if esquema == "upwind":
            passo_gpu_upwind(u_gpu, u_gpu_new, dx, dt, NU)
        else:
            passo_gpu_central(u_gpu, u_gpu_new, dx, dt, NU)

        u_gpu, u_gpu_new = u_gpu_new, u_gpu

        if salvar_snapshots:
            t_atual = (n + 1) * dt
            for ts in tempos_snap:
                if ts not in snapshots and abs(t_atual - ts) <= 0.5 * dt:
                    snapshots[ts] = cp.asnumpy(u_gpu)

    cp.cuda.Stream.null.synchronize()
    elapsed = time.perf_counter() - t0

    u_num = cp.asnumpy(u_gpu)
    u_ex = burgers_analitica(x, T_FINAL)

    return {
        "x": x,
        "u_num": u_num,
        "u_ex": u_ex,
        "u0": u0,
        "dx": dx,
        "dt": dt,
        "nt": nt,
        "tempo_execucao": elapsed,
        "snapshots": snapshots,
    }


# ============================================================
# 7) SIMULAÇÃO CPU COM NUMPY
# ============================================================
def simular_cpu(Nx, esquema):
    x = np.linspace(X0, XL, Nx, endpoint=False, dtype=np.float64)
    dx = (XL - X0) / Nx
    u = burgers_analitica(x, 0.0)
    dt, nt = calcular_dt_explicito(u, dx)

    t0 = time.perf_counter()
    for _ in range(nt):
        if esquema == "upwind":
            u = passo_cpu_upwind(u, dx, dt)
        else:
            u = passo_cpu_central(u, dx, dt)
    elapsed = time.perf_counter() - t0

    u_ex = burgers_analitica(x, T_FINAL)
    return {
        "x": x,
        "u_num": u,
        "u_ex": u_ex,
        "dx": dx,
        "dt": dt,
        "nt": nt,
        "tempo_execucao": elapsed,
    }


# ============================================================
# 8) UTILITÁRIOS DE SALVAMENTO
# ============================================================
def salvar_csv_erros(resultados, caminho_csv):
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "esquema", "Nx", "dx", "dt", "nt",
            "erro_L2_rel", "erro_Linf_rel", "tempo_execucao_s"
        ])
        for esquema, dados in resultados.items():
            for linha in dados:
                writer.writerow([
                    esquema,
                    linha["Nx"],
                    linha["dx"],
                    linha["dt"],
                    linha["nt"],
                    linha["L2"],
                    linha["Linf"],
                    linha["tempo_execucao"],
                ])


def salvar_csv_ordens(ordens_dict, caminho_csv):
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["esquema", "Nx_i", "Nx_ip1", "ordem_L2"])
        for esquema, itens in ordens_dict.items():
            for item in itens:
                writer.writerow([esquema, item[0], item[1], item[2]])


def salvar_csv_cpu_gpu(comparacoes, caminho_csv):
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "esquema", "Nx", "backend", "dx", "dt", "nt",
            "erro_L2_rel", "erro_Linf_rel", "tempo_execucao_s"
        ])
        for linha in comparacoes:
            writer.writerow(linha)


# ============================================================
# 9) EXECUÇÃO PRINCIPAL
# ============================================================
def main():
    # Apenas força a inicialização do dispositivo e mostra o nome da GPU
    try:
        device = cp.cuda.runtime.getDevice()
        props = cp.cuda.runtime.getDeviceProperties(device)
        nome_gpu = props["name"].decode() if isinstance(props["name"], bytes) else props["name"]
        print(f"GPU detectada pelo CuPy: {nome_gpu}\n")
    except Exception as exc:
        raise RuntimeError(
            "Não foi possível inicializar o CuPy/CUDA. Verifique a instalação do CuPy e do driver NVIDIA."
        ) from exc

    resultados_erros = {"upwind": [], "central": []}
    resultados_malha_fina = {}
    resultados_todas_malhas = {"upwind": [], "central": []}

    print("Iniciando estudo de convergência na GPU com CuPy...\n")

    for esquema in ["upwind", "central"]:
        print(f"=== Esquema: {esquema} ===")

        for Nx in REFINAMENTOS:
            saida = simular_gpu(
                Nx=Nx,
                esquema=esquema,
                salvar_snapshots=(Nx == REFINAMENTOS[-1])
            )

            eL2 = erro_l2_rel(saida["u_num"], saida["u_ex"])
            eLinf = erro_linf_rel(saida["u_num"], saida["u_ex"])

            linha = {
                "Nx": Nx,
                "dx": saida["dx"],
                "dt": saida["dt"],
                "nt": saida["nt"],
                "L2": eL2,
                "Linf": eLinf,
                "tempo_execucao": saida["tempo_execucao"],
            }
            resultados_erros[esquema].append(linha)
            resultados_todas_malhas[esquema].append((Nx, saida["x"], saida["u_num"], saida["u_ex"]))

            if Nx == REFINAMENTOS[-1]:
                resultados_malha_fina[esquema] = saida

            print(
                f"Nx = {Nx:4d} | dx = {saida['dx']:.6e} | dt = {saida['dt']:.6e} "
                f"| nt = {saida['nt']:6d} | L2 = {eL2:.6e} | Linf = {eLinf:.6e} "
                f"| t_exec = {saida['tempo_execucao']:.6f} s"
            )
        print()

    # --------------------------------------------------------
    # Ordens observadas
    # --------------------------------------------------------
    ordens_dict = {"upwind": [], "central": []}
    for esquema in ["upwind", "central"]:
        erros = np.array([d["L2"] for d in resultados_erros[esquema]])
        hs = np.array([d["dx"] for d in resultados_erros[esquema]])
        p_obs = ordem_observada(erros, hs)

        print(f"Ordem observada em L2 para {esquema}:")
        for i, p in enumerate(p_obs):
            n0 = REFINAMENTOS[i]
            n1 = REFINAMENTOS[i + 1]
            ordens_dict[esquema].append((n0, n1, p))
            print(f"de Nx={n0} para Nx={n1} -> p = {p:.6f}")
        print()

    # --------------------------------------------------------
    # Comparação CPU x GPU em malha grosseira
    # --------------------------------------------------------
    print("Comparando CPU x GPU em malha grosseira...\n")
    comparacoes_cpu_gpu_csv = []
    perfis_cpu_gpu = {}

    for esquema in ["upwind", "central"]:
        gpu = simular_gpu(NX_CPU_COMPARACAO, esquema)
        cpu = simular_cpu(NX_CPU_COMPARACAO, esquema)

        eL2_gpu = erro_l2_rel(gpu["u_num"], gpu["u_ex"])
        eLinf_gpu = erro_linf_rel(gpu["u_num"], gpu["u_ex"])
        eL2_cpu = erro_l2_rel(cpu["u_num"], cpu["u_ex"])
        eLinf_cpu = erro_linf_rel(cpu["u_num"], cpu["u_ex"])

        comparacoes_cpu_gpu_csv.append([
            esquema, NX_CPU_COMPARACAO, "GPU_CuPy", gpu["dx"], gpu["dt"], gpu["nt"],
            eL2_gpu, eLinf_gpu, gpu["tempo_execucao"]
        ])
        comparacoes_cpu_gpu_csv.append([
            esquema, NX_CPU_COMPARACAO, "CPU_NumPy", cpu["dx"], cpu["dt"], cpu["nt"],
            eL2_cpu, eLinf_cpu, cpu["tempo_execucao"]
        ])

        speedup = cpu["tempo_execucao"] / gpu["tempo_execucao"] if gpu["tempo_execucao"] > 0 else math.inf

        perfis_cpu_gpu[esquema] = {
            "x": gpu["x"],
            "u_ex": gpu["u_ex"],
            "u_gpu": gpu["u_num"],
            "u_cpu": cpu["u_num"],
            "speedup": speedup,
        }

        print(
            f"{esquema}: CPU = {cpu['tempo_execucao']:.6f} s | "
            f"GPU = {gpu['tempo_execucao']:.6f} s | speedup = {speedup:.3f}"
        )
    print()

    # --------------------------------------------------------
    # Salvar CSVs
    # --------------------------------------------------------
    salvar_csv_erros(resultados_erros, os.path.join(PASTA_DADOS, "erros_convergencia_gpu_cupy.csv"))
    salvar_csv_ordens(ordens_dict, os.path.join(PASTA_DADOS, "ordens_observadas_cupy.csv"))
    salvar_csv_cpu_gpu(comparacoes_cpu_gpu_csv, os.path.join(PASTA_DADOS, "comparacao_cpu_gpu_cupy.csv"))

    # --------------------------------------------------------
    # Gráfico 1: perfis na malha mais fina
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    plt.plot(
        resultados_malha_fina["upwind"]["x"],
        resultados_malha_fina["upwind"]["u_ex"],
        "k-",
        linewidth=3,
        label="Analítica"
    )
    plt.plot(
        resultados_malha_fina["upwind"]["x"],
        resultados_malha_fina["upwind"]["u_num"],
        "--",
        linewidth=2,
        label="GPU CuPy Upwind"
    )
    plt.plot(
        resultados_malha_fina["central"]["x"],
        resultados_malha_fina["central"]["u_num"],
        "-.",
        linewidth=2,
        label="GPU CuPy Central"
    )
    plt.xlabel("x")
    plt.ylabel("u(x, t_final)")
    plt.title(f"Burgers viscosa em t = {T_FINAL} - malha mais fina")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_GRAFICOS, "perfil_malha_fina_gpu_cupy.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # Gráfico 2: todas as malhas contra a analítica (Upwind)
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    x_ref = resultados_todas_malhas["upwind"][-1][1]
    u_ref = resultados_todas_malhas["upwind"][-1][3]
    plt.plot(x_ref, u_ref, "k-", linewidth=3, label="Analítica")
    for Nx, x, u_num, _ in resultados_todas_malhas["upwind"]:
        plt.plot(x, u_num, linewidth=1.8, label=f"Upwind Nx={Nx}")
    plt.xlabel("x")
    plt.ylabel("u(x, t_final)")
    plt.title("Perfis Upwind para todas as malhas")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_GRAFICOS, "perfis_todas_malhas_upwind_cupy.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # Gráfico 3: todas as malhas contra a analítica (Central)
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    x_ref = resultados_todas_malhas["central"][-1][1]
    u_ref = resultados_todas_malhas["central"][-1][3]
    plt.plot(x_ref, u_ref, "k-", linewidth=3, label="Analítica")
    for Nx, x, u_num, _ in resultados_todas_malhas["central"]:
        plt.plot(x, u_num, linewidth=1.8, label=f"Central Nx={Nx}")
    plt.xlabel("x")
    plt.ylabel("u(x, t_final)")
    plt.title("Perfis diferença central para todas as malhas")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_GRAFICOS, "perfis_todas_malhas_central_cupy.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # Gráfico 4: convergência L2
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    plt.loglog(
        [d["dx"] for d in resultados_erros["upwind"]],
        [d["L2"] for d in resultados_erros["upwind"]],
        "o-",
        linewidth=2,
        markersize=7,
        label="Upwind"
    )
    plt.loglog(
        [d["dx"] for d in resultados_erros["central"]],
        [d["L2"] for d in resultados_erros["central"]],
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
    plt.savefig(os.path.join(PASTA_GRAFICOS, "convergencia_L2_cupy.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # Gráfico 5: convergência Linf
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    plt.loglog(
        [d["dx"] for d in resultados_erros["upwind"]],
        [d["Linf"] for d in resultados_erros["upwind"]],
        "o-",
        linewidth=2,
        markersize=7,
        label="Upwind"
    )
    plt.loglog(
        [d["dx"] for d in resultados_erros["central"]],
        [d["Linf"] for d in resultados_erros["central"]],
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
    plt.savefig(os.path.join(PASTA_GRAFICOS, "convergencia_Linf_cupy.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # Gráfico 6 e 7: snapshots da malha mais fina
    # --------------------------------------------------------
    for esquema in ["upwind", "central"]:
        plt.figure(figsize=(10, 6))
        snaps = resultados_malha_fina[esquema]["snapshots"]
        for ts in sorted(snaps.keys()):
            plt.plot(resultados_malha_fina[esquema]["x"], snaps[ts], label=f"t={ts:.2f}")
        plt.xlabel("x")
        plt.ylabel("u(x,t)")
        plt.title(f"Snapshots temporais - {esquema} - malha mais fina")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PASTA_GRAFICOS, f"snapshots_{esquema}_cupy.png"), dpi=300, bbox_inches="tight")
        plt.close()

    # --------------------------------------------------------
    # Gráfico 8 e 9: comparação CPU x GPU na malha grosseira
    # --------------------------------------------------------
    for esquema in ["upwind", "central"]:
        plt.figure(figsize=(10, 6))
        perf = perfis_cpu_gpu[esquema]
        plt.plot(perf["x"], perf["u_ex"], "k-", linewidth=3, label="Analítica")
        plt.plot(perf["x"], perf["u_cpu"], "--", linewidth=2, label="CPU NumPy")
        plt.plot(perf["x"], perf["u_gpu"], "-.", linewidth=2, label="GPU CuPy")
        plt.xlabel("x")
        plt.ylabel("u(x, t_final)")
        plt.title(
            f"CPU x GPU - {esquema} - Nx={NX_CPU_COMPARACAO} - speedup={perf['speedup']:.2f}"
        )
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PASTA_GRAFICOS, f"cpu_gpu_{esquema}_cupy.png"), dpi=300, bbox_inches="tight")
        plt.close()

    # --------------------------------------------------------
    # Resumo no terminal
    # --------------------------------------------------------
    print("Resumo final:")
    for esquema in ["upwind", "central"]:
        print(f"\nEsquema: {esquema}")
        print(" Nx        dx              L2_rel           Linf_rel           t_exec(s)")
        for linha in resultados_erros[esquema]:
            print(
                f"{linha['Nx']:4d}   {linha['dx']: .6e}   {linha['L2']: .6e}   "
                f"{linha['Linf']: .6e}   {linha['tempo_execucao']: .6e}"
            )

    print("\nArquivos salvos:")
    print(f"- Gráficos em: {PASTA_GRAFICOS}")
    print(f"- Tabelas CSV em: {PASTA_DADOS}")


if __name__ == "__main__":
    main()
