import numpy as np
from params import CavityConfig, MeshType, MeshTypes, DiscretizationTypes
import matplotlib.pyplot as plt


def gerar_malha(config: CavityConfig, disc: DiscretizationTypes):
    if disc == DiscretizationTypes.C:
        dx = config.lx / (config.nx - 1)
        dy = config.ly / (config.ny - 1)
        x = np.linspace(0, config.lx+2*dx, config.nx+2)
        y = np.linspace(0, config.ly+2*dy, config.ny+2)
        X, Y = np.meshgrid(x, y)
        return X, Y
    else:
        raise NotImplementedError("Cenas dos próximos capítulos...")


def plotar_malha(ax, X: np.ndarray, Y: np.ndarray, color: str, label: str, linestyle: str = "-", size: int = 20):
    ax.plot(X, Y, color=color, linestyle=linestyle, linewidth=0.8)
    ax.plot(X.T, Y.T, color=color, linestyle=linestyle, linewidth=0.8)
    ax.scatter(X, Y, color=color, s=size, label=label)


def configurar_legenda_fora(fig, ax):
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0)
    fig.tight_layout()


def vizualizar_malha(X: np.ndarray, Y: np.ndarray, mesh_type: MeshType):
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
        plt.show()
    elif mesh_type.type == MeshTypes.DF:
        PX = X[1:-1, 1:-1]
        PY = Y[1:-1, 1:-1]
        UX = X[1:-1, 2:]
        UY = Y[1:-1, 2:]
        VX = X[2:, 1:-1]
        VY = Y[2:, 1:-1]
        fig, ax = plt.subplots()
        plotar_malha(ax, PX, PY, color="tab:blue", label="Pontos de Pressão")
        plotar_malha(ax, UX, UY, color="tab:red", label="Pontos de Velocidade U", linestyle="--", size=5)
        plotar_malha(ax, VX, VY, color="tab:green", label="Pontos de Velocidade V", linestyle=":", size=5)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(f"Malha {mesh_type.type}")
        ax.set_aspect("equal")
        configurar_legenda_fora(fig, ax)
        plt.show()
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
        plt.show()
    else:
        raise NotImplementedError("Cenas dos próximos capítulos...")
