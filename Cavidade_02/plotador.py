import numpy as np
import matplotlib.pyplot as plt


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
    valor_alvo=1.0
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

    plt.show()

    return fig, ax