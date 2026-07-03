import numpy as np
from params import CavityConfig, MeshType, MeshTypes, DiscretizationTypes
from matplotlib_config import configurar_matplotlib

matplotlib = configurar_matplotlib()
import matplotlib.pyplot as plt


def _mostrar_se_interativo():
    if matplotlib.get_backend().lower() != "agg":
        plt.show()


def gerar_malha(config: CavityConfig, disc: DiscretizationTypes):
    if disc == DiscretizationTypes.C:
        dx = config.lx / (config.nx - 1)
        dy = config.ly / (config.ny - 1)
        x = np.linspace(-dx/2, config.lx+dx/2, config.nx+2, endpoint=True)
        y = np.linspace(-dy/2, config.ly+dy/2, config.ny+2, endpoint=True)
        X, Y = np.meshgrid(x, y)
        return x, y
    else:
        raise NotImplementedError("Cenas dos próximos capítulos...")


def plotar_malha(ax, XY :np.meshgrid , color: str, label: str, linestyle: str = "-", size: int = 20):
    X, Y = XY
    ax.plot(X, Y, color=color, linestyle=linestyle, linewidth=0.8)
    ax.plot(X.T, Y.T, color=color, linestyle=linestyle, linewidth=0.8)
    ax.scatter(X, Y, color=color, s=size, label=label)


def configurar_legenda_fora(fig, ax):
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0)
    fig.tight_layout()


def vizualizar_malha(X: np.ndarray, Y: np.ndarray, mesh_type: MeshType, config: CavityConfig = CavityConfig()):
    if mesh_type.type is None:
        raise ValueError("O tipo de malha deve ser especificado para a visualização.")
    elif mesh_type.type == MeshTypes.CL:
        fig, ax = plt.subplots()
        plotar_malha(ax, X, Y, color="tab:blue", label="Malha Colocalizada")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(f"Malha {mesh_type.type}")
        ax.set_aspect("equal")
        configurar_legenda_fora(fig, ax)
        _mostrar_se_interativo()
    elif mesh_type.type == MeshTypes.DF:
        # PX = X[1:-1, 1:-1]
        # PY = Y[1:-1, 1:-1]
        # UX = X[1:-1, 2:]-config.dx/2
        # UY = Y[1:-1, 2:]
        # VX = X[2:, 1:-1]
        # VY = Y[2:, 1:-1]-config.dy/2
        PX = X[1:-1]
        PY = Y[1:-1]
        UX = X[2:]
        UY = Y[1:-1]
        VX = X[ 1:-1]
        VY = Y[2:]
        fig, ax = plt.subplots()
        plotar_malha(ax, np.meshgrid(PX, PY), color="tab:blue", label="Pontos de Pressão")
        plotar_malha(ax, np.meshgrid(UX, UY), color="tab:red", label="Pontos de Velocidade U", linestyle="--", size=5)
        plotar_malha(ax, np.meshgrid(VX, VY), color="tab:green", label="Pontos de Velocidade V", linestyle=":", size=5)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(f"Malha {mesh_type.type}")
        ax.set_aspect("equal")
        configurar_legenda_fora(fig, ax)
        _mostrar_se_interativo()
    elif mesh_type.type == MeshTypes.DB:
        PX = X[1:-1, 1:-1]
        PY = Y[1:-1, 1:-1]
        UX = X[1:-1, :-2]
        UY = Y[1:-1, :-2]
        VX = X[:-2, 1:-1]
        VY = Y[:-2, 1:-1]
        fig, ax = plt.subplots()
        plotar_malha(ax, PX, PY, color="tab:blue", label="Pontos de Pressão")
        plotar_malha(ax, UX, UY, color="tab:red", label="Pontos de Velocidade U", linestyle="--")
        plotar_malha(ax, VX, VY, color="tab:green", label="Pontos de Velocidade V", linestyle=":")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(f"Malha {mesh_type.type}")
        ax.set_aspect("equal")
        configurar_legenda_fora(fig, ax)
        _mostrar_se_interativo()
    else:
        raise NotImplementedError("Cenas dos próximos capítulos...")
