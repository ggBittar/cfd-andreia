import numpy as np
from matplotlib_config import configurar_matplotlib

matplotlib = configurar_matplotlib()
import matplotlib.pyplot as plt

from params import CavityConfig, DiscretizationTypes, MeshType, MeshTypes, criar_condicoes_iniciais
from malhas import gerar_malha, vizualizar_malha, plotar_malha
from solver import simular
from plotador import plotar_campo_velocidade, plotar_perfis_ghia

config = CavityConfig()
initial_conditions = criar_condicoes_iniciais(config)

mesh_type = MeshType(type=MeshTypes.DF)  # "C", "DF" ou "DB"
disc_type = DiscretizationTypes.C  # "A" para volume nulo, "B" para semi-volume, "C" para célula fantasma

x, y = gerar_malha(config, disc_type)

X, Y = np.meshgrid(x, y)
X_fisico, Y_fisico = np.meshgrid(x[1:-1], y[1:-1])
print("Configurações da Cavidade:")
print(f"  - Dimensões: {config.nx} x {config.ny}")
print(f"  - Domínio: [{config.lx}, {config.ly}]")
print(f"  - Viscosidade cinemática: {config.nu}")
print(f"  - Número de Reynolds: {config.Re}")
print(f"  - Passo de tempo: {config.dt}")
print(f"  - dx: {config.dx}, dy: {config.dy}")
print(f"  - SOR: w={config.sor_w}, tolerância={config.sor_tolerance}, iterações máximas={config.sor_max_iter}")
print(
    "  - Parada:"
    f" {'resíduo RMS estacionário' if config.stop_by_convergence else 'tempo final'}"
    f" | tolerância={config.convergence_tolerance}"
)

if config.plot_mesh:
    vizualizar_malha(x, y, mesh_type, config)

u, v, P, historico = simular(config, initial_conditions)

print("\nHistórico da simulação:")
for info in historico:
    if info["step"] == 1 or info["step"] % config.report_interval == 0 or info == historico[-1]:
        print(
            f"  passo={info['step']:5d} "
            f"t={info['time']:.5f} "
            f"mass_rms={info['mass_error']:.3e} "
            f"mass_max={info['mass_error_max']:.3e} "
            f"res_conv={info['convergence_residual']:.3e} "
            f"sor_iter={info['sor_iter']:4d} "
            f"sor_erro={info['sor_error']:.3e}"
        )

if historico:
    ultimo = historico[-1]
    print(
        "\nResultado final:"
        f"\n  - passos executados: {ultimo['step']}"
        f"\n  - tempo simulado: {ultimo['time']:.5f} s"
        f"\n  - erro RMS de massa: {ultimo['mass_error']:.3e}"
        f"\n  - erro máximo de massa: {ultimo['mass_error_max']:.3e}"
        f"\n  - resíduo de convergência: {ultimo['convergence_residual']:.3e}"
    )
    if config.stop_by_convergence and ultimo["convergence_residual"] < config.convergence_tolerance:
        print("  - critério de parada: convergência")
    elif ultimo["time"] >= config.t_final:
        print("  - critério de parada: t_final")
    else:
        print("  - critério de parada: max_steps")

if config.plot_results:
    fig, ax = plotar_campo_velocidade(
        X_fisico,
        Y_fisico,
        u[1:-1, 1:-1],
        v[1:-1, 1:-1],
        tipo="streamplot",
        titulo="Cavidade com tampa deslizante",
        valor_alvo=config.u_max,
        mostrar=False,
    )

    plotar_malha(ax, (X_fisico, Y_fisico), color="tab:blue", label="Pontos da Malha", linestyle="-", size=5)
    ax.set_xlim(0.0, config.lx)
    ax.set_ylim(0.0, config.ly)
    if matplotlib.get_backend().lower() != "agg":
        plt.show()
    
if config.plot_results_2:
    fig, ax = plotar_campo_velocidade(
        X,
        Y,
        u,
        v,
        tipo="streamplot",
        titulo="Cavidade com tampa deslizante",
        valor_alvo=config.u_max,
        mostrar=False,
    )

    plotar_malha(ax, (X, Y), color="tab:blue", label="Pontos da Malha", linestyle="-", size=5)
    ax.set_xlim(0.0, config.lx)
    ax.set_ylim(0.0, config.ly)
    ax.set
    if matplotlib.get_backend().lower() != "agg":
        plt.show()

if config.plot_profiles:
    plotar_perfis_ghia(
        x[1:-1],
        y[1:-1],
        u[1:-1, 1:-1],
        v[1:-1, 1:-1],
        re=config.Re,
        comparar_ghia=config.plot_ghia_reference,
    )
