import numpy as np
from matplotlib_config import configurar_matplotlib

matplotlib = configurar_matplotlib()
import matplotlib.pyplot as plt


GHIA_RE100_U_Y = np.array([
    [1.0000, 1.00000],
    [0.9766, 0.84123],
    [0.9688, 0.78871],
    [0.9609, 0.73722],
    [0.9531, 0.68717],
    [0.8516, 0.23151],
    [0.7344, 0.00332],
    [0.6172, -0.13641],
    [0.5000, -0.20581],
    [0.4531, -0.21090],
    [0.2813, -0.15662],
    [0.1719, -0.10150],
    [0.1016, -0.06434],
    [0.0703, -0.04775],
    [0.0625, -0.04192],
    [0.0547, -0.03717],
    [0.0000, 0.00000],
])


GHIA_RE100_X_V = np.array([
    [1.0000, 0.00000],
    [0.9688, -0.05906],
    [0.9609, -0.07391],
    [0.9531, -0.08864],
    [0.9453, -0.10313],
    [0.9063, -0.16914],
    [0.8594, -0.22445],
    [0.8047, -0.24533],
    [0.5000, 0.05454],
    [0.2344, 0.17527],
    [0.2266, 0.17507],
    [0.1563, 0.16077],
    [0.0938, 0.12317],
    [0.0781, 0.10890],
    [0.0703, 0.10091],
    [0.0625, 0.09233],
    [0.0000, 0.00000],
])


def _mostrar_se_interativo():
    if matplotlib.get_backend().lower() != "agg":
        plt.show()


def perfis_linhas_centrais(x, y, u, v):
    x = np.asarray(x)
    y = np.asarray(y)
    u = np.asarray(u)
    v = np.asarray(v)

    i_centro = int(np.argmin(np.abs(x - 0.5 * (x[0] + x[-1]))))
    j_centro = int(np.argmin(np.abs(y - 0.5 * (y[0] + y[-1]))))

    return {
        "x_centro": float(x[i_centro]),
        "y_centro": float(y[j_centro]),
        "y": y,
        "u_vertical": u[:, i_centro],
        "x": x,
        "v_horizontal": v[j_centro, :],
    }


def plotar_perfis_ghia(
    x,
    y,
    u,
    v,
    re=None,
    comparar_ghia=True,
    mostrar=True,
    salvar_em=None,
):
    perfis = perfis_linhas_centrais(x, y, u, v)
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    axs[0].plot(perfis["u_vertical"], perfis["y"], "o-", label=f"Presente x={perfis['x_centro']:.4f}")
    axs[0].set_xlabel("u")
    axs[0].set_ylabel("y")
    axs[0].set_title("Perfil u x y na linha vertical central")
    axs[0].grid(True, alpha=0.3)

    axs[1].plot(perfis["x"], perfis["v_horizontal"], "o-", label=f"Presente y={perfis['y_centro']:.4f}")
    axs[1].set_xlabel("x")
    axs[1].set_ylabel("v")
    axs[1].set_title("Perfil x x v na linha horizontal central")
    axs[1].grid(True, alpha=0.3)

    if comparar_ghia and re is not None and np.isclose(float(re), 100.0):
        axs[0].plot(GHIA_RE100_U_Y[:, 1], GHIA_RE100_U_Y[:, 0], "ks", fillstyle="none", label="Ghia Re=100")
        axs[1].plot(GHIA_RE100_X_V[:, 0], GHIA_RE100_X_V[:, 1], "ks", fillstyle="none", label="Ghia Re=100")

    for ax in axs:
        ax.legend()

    fig.tight_layout()

    if salvar_em is not None:
        fig.savefig(salvar_em, dpi=300, bbox_inches="tight")

    if mostrar:
        _mostrar_se_interativo()

    return fig, axs


def plotar_campo_velocidade(
    X,
    Y,
    U,
    V,
    tipo="quiver",
    titulo="Campo de velocidade",
    escala_vetores=None,
    densidade=1.5,
    cmap="viridis",
    mostrar_magnitude=True,
    salvar_em=None,
    figsize=(8, 6),
    valor_alvo=1.0,
    mostrar=True
):
    """
    Plota um campo de velocidade 2D.

    Parâmetros
    ----------
    X, Y : array_like
        Matrizes com as coordenadas da malha.
        Normalmente geradas por np.meshgrid.

    U, V : array_like
        Componentes da velocidade nas direções x e y.

    tipo : str
        Tipo de gráfico:
        - "quiver"     : vetores de velocidade
        - "streamplot" : linhas de corrente
        - "contour"    : mapa da magnitude da velocidade
        - "completo"   : contour + streamplot + quiver

    titulo : str
        Título do gráfico.

    escala_vetores : float ou None
        Escala dos vetores no quiver.
        Se None, o matplotlib escolhe automaticamente.

    densidade : float
        Densidade das linhas de corrente no streamplot.

    cmap : str
        Mapa de cores usado para a magnitude.

    mostrar_magnitude : bool
        Se True, mostra a barra de cores da magnitude.

    salvar_em : str ou None
        Caminho para salvar a figura.
        Exemplo: "campo_velocidade.png"

    figsize : tuple
        Tamanho da figura.

    Retorno
    -------
    fig, ax
        Objetos da figura e dos eixos do matplotlib.
    """

    X = np.asarray(X)
    Y = np.asarray(Y)
    U = np.asarray(U)
    V = np.asarray(V)

    if X.shape != Y.shape or X.shape != U.shape or X.shape != V.shape:
        raise ValueError("X, Y, U e V devem ter o mesmo formato.")

    magnitude = np.sqrt(U**2 + V**2)
    
   
    tolerancia = 0.2

    faixa = np.where(
        (magnitude >= valor_alvo - tolerancia) &
        (magnitude <= valor_alvo + tolerancia),
        magnitude,
        np.nan
    )


    fig, ax = plt.subplots(figsize=figsize)

    tipo = tipo.lower()

    if tipo == "contour":
        grafico = ax.contourf(X, Y, magnitude, levels=30, cmap=cmap)

        if mostrar_magnitude:
            cbar = fig.colorbar(grafico, ax=ax)
            cbar.set_label("Magnitude da velocidade")
        ax.contourf(
            X,
            Y,
            faixa,
            levels=[valor_alvo - tolerancia, valor_alvo + tolerancia],
            colors=["red"],
            alpha=0.5
        )

    elif tipo == "quiver":
        if mostrar_magnitude:
            grafico = ax.contourf(X, Y, magnitude, levels=30, cmap=cmap, alpha=0.75)
            cbar = fig.colorbar(grafico, ax=ax)
            cbar.set_label("Magnitude da velocidade")

        ax.quiver(
            X,
            Y,
            U,
            V,
            color="black",
            scale=escala_vetores
        )
        ax.contourf(
            X,
            Y,
            faixa,
            levels=[valor_alvo - tolerancia, valor_alvo + tolerancia],
            colors=["red"],
            alpha=0.5
        )

    elif tipo == "streamplot":
        grafico = ax.contourf(X, Y, magnitude, levels=30, cmap=cmap, alpha=0.75)

        if mostrar_magnitude:
            cbar = fig.colorbar(grafico, ax=ax)
            cbar.set_label("Magnitude da velocidade")

        ax.streamplot(
            X,
            Y,
            U,
            V,
            color="black",
            density=densidade
        )
        ax.contourf(
            X,
            Y,
            faixa,
            levels=[valor_alvo - tolerancia, valor_alvo + tolerancia],
            colors=["red"],
            alpha=0.5
        )

    elif tipo == "completo":
        grafico = ax.contourf(X, Y, magnitude, levels=30, cmap=cmap, alpha=0.75)

        if mostrar_magnitude:
            cbar = fig.colorbar(grafico, ax=ax)
            cbar.set_label("Magnitude da velocidade")

        ax.streamplot(
            X,
            Y,
            U,
            V,
            color="white",
            density=densidade,
            linewidth=1
        )

        ax.quiver(
            X,
            Y,
            U,
            V,
            color="black",
            scale=escala_vetores
        )
        ax.contourf(
            X,
            Y,
            faixa,
            levels=[valor_alvo - tolerancia, valor_alvo + tolerancia],
            colors=["red"],
            alpha=0.5
        )

    else:
        raise ValueError(
            "tipo deve ser 'quiver', 'streamplot', 'contour' ou 'completo'."
        )

    ax.set_title(titulo)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if salvar_em is not None:
        plt.savefig(salvar_em, dpi=300, bbox_inches="tight")

    if mostrar:
        _mostrar_se_interativo()

    return fig, ax
