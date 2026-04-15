import numpy as np
import matplotlib.pyplot as plt
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
import os
from matplotlib.patches import Rectangle

# ============================================================
# 1) DADOS DO PROBLEMA
# ============================================================
# Chapa retangular 2D em regime transiente.
# Nesta versão, a malha é NODE-CENTERED:
# - as incógnitas ficam nos NÓS da malha;
# - os nós de contorno ficam exatamente nas paredes;
# - os volumes de controle são construídos ao redor dos nós;
# - por isso, nas bordas há SEMIVOLUMES;
# - nos cantos há QUARTOS DE VOLUME.

L = 0.02            # comprimento em x (m)
H = 0.01            # altura/espessura em y (m)
T_inf = 30.0        # temperatura ambiente (°C)
T0 = 30.0           # temperatura inicial (°C)
h = 20.0            # coeficiente convectivo (W/m²K)
q_flux = 5.0e4      # fluxo imposto em duas regiões da base (W/m²)
k = 14.9            # condutividade térmica (W/mK)
alpha = 3.95e-6     # difusividade térmica (m²/s)
t_final = 60.0      # tempo final (s)

# A partir de alpha = k / (rho*cp)
rho_cp = k / alpha

# ============================================================
# 2) MALHA NODE-CENTERED
# ============================================================
# Agora os pontos ficam nos nós, incluindo as paredes:
# x = 0, dx, 2dx, ..., L
# y = 0, dy, 2dy, ..., H
#
# Se você quiser mais pontos, aumente Nx e Ny.
# Aqui Nx e Ny representam NÚMERO DE NÓS.
Nx = 21
Ny = 11

# Como os nós incluem as extremidades, o passo é dividido por (N-1)
dx = L / (Nx - 1)
dy = H / (Ny - 1)

x_nodes = np.linspace(0.0, L, Nx)
y_nodes = np.linspace(0.0, H, Ny)

# Passo de tempo
# Como o esquema é implícito, ele é estável para passos maiores,
# mas ainda assim mantemos um valor razoável para boa resolução temporal.
dt = 0.1
nt = int(round(t_final / dt))

# Profundidade unitária do problema 2D
depth = 1.0

# ============================================================
# 3) PASTAS DE SAÍDA
# ============================================================
os.makedirs("graficos", exist_ok=True)

# A cada quantos segundos salvar o campo de temperatura
save_field_interval = 12.0
save_times = np.arange(0.0, t_final + 0.5 * save_field_interval, save_field_interval)

# ============================================================
# 4) FUNÇÕES AUXILIARES
# ============================================================
def idx(i, j):
    """
    Converte o índice 2D (i, j) em índice 1D.

    i -> direção x
    j -> direção y
    """
    return j * Nx + i


def is_heat_flux_region(x):
    """
    Retorna True se a posição x estiver em uma das regiões da base
    onde o fluxo de calor é imposto.

    Regiões aquecidas em y = 0:
      0.003 <= x <= 0.008
      0.012 <= x <= 0.017
    """
    return (0.003 <= x <= 0.008) or (0.012 <= x <= 0.017)


def cv_width(i):
    """
    Largura do volume de controle associado ao nó i.

    Em malha node-centered:
    - nós internos -> largura = dx
    - nós na esquerda/direita -> largura = dx/2
    """
    if i == 0 or i == Nx - 1:
        return dx / 2.0
    return dx


def cv_height(j):
    """
    Altura do volume de controle associado ao nó j.

    Em malha node-centered:
    - nós internos -> altura = dy
    - nós em baixo/cima -> altura = dy/2
    """
    if j == 0 or j == Ny - 1:
        return dy / 2.0
    return dy


# ============================================================
# 5) CONDIÇÃO INICIAL
# ============================================================
# Como as incógnitas ficam nos nós, agora T[j, i] representa a
# temperatura diretamente no nó (x_i, y_j).
T = np.full((Ny, Nx), T0, dtype=float)

# Pontos pedidos no enunciado
# Aqui, como a malha é node-centered, os pontos de contorno podem
# coincidir exatamente com nós da borda, dependendo do refinamento.
def nearest_i(x_target):
    return int(np.argmin(np.abs(x_nodes - x_target)))


def nearest_j(y_target):
    return int(np.argmin(np.abs(y_nodes - y_target)))


i_probe = nearest_i(0.01)
j_probe_bottom = nearest_j(0.0)
j_probe_mid = nearest_j(0.005)
j_probe_top = nearest_j(0.01)

time_history = []
T_bottom_history = []
T_mid_history = []
T_top_history = []


# ============================================================
# 6) VISUALIZAÇÃO DA MALHA NODE-CENTERED COM SEMIVOLUMES
# ============================================================
def plot_node_centered_mesh():
    """
    Desenha a malha node-centered de forma geométrica correta:
    - volumes internos inteiros
    - semivolumes nas bordas
    - quartos de volume nos cantos
    - nós da malha
    - regiões com fluxo de calor imposto na base
    - pontos monitorados
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Desenha os volumes de controle como retângulos individuais.
    # Assim, as bordas aparecem realmente como semivolumes.
    for j in range(Ny):
        for i in range(Nx):
            w = cv_width(i)
            h_cv = cv_height(j)

            # O nó (x_i, y_j) fica no CENTRO do volume de controle,
            # exceto que, nas bordas, metade do volume fica "para dentro"
            # do domínio e a outra metade não existe fora do domínio.
            x0 = x_nodes[i] - w / 2.0
            y0 = y_nodes[j] - h_cv / 2.0

            # Mantemos o desenho recortado ao domínio físico.
            x0 = max(0.0, x0)
            y0 = max(0.0, y0)

            rect = Rectangle(
                (x0, y0), w, h_cv,
                fill=False, edgecolor='black', linewidth=1.0
            )
            ax.add_patch(rect)

    # Nós da malha
    Xn, Yn = np.meshgrid(x_nodes, y_nodes)
    ax.scatter(Xn, Yn, s=30, label='Nós da malha (incógnitas)')

    # Marca na base as regiões com fluxo de calor imposto.
    # Aqui desenhamos a face sul aquecida.
    for i in range(Nx - 1):
        x_left = x_nodes[i]
        x_right = x_nodes[i + 1]
        x_mid = 0.5 * (x_left + x_right)
        if is_heat_flux_region(x_mid):
            ax.plot([x_left, x_right], [0.0, 0.0], linewidth=5, label='Fluxo de calor imposto' if i == 0 else None)

    # Pontos monitorados
    ax.scatter(x_nodes[i_probe], y_nodes[j_probe_bottom], s=120, marker='s', label='Ponto próximo de (0.01, 0)')
    ax.scatter(x_nodes[i_probe], y_nodes[j_probe_mid], s=120, marker='^', label='Ponto próximo de (0.01, 0.005)')
    ax.scatter(x_nodes[i_probe], y_nodes[j_probe_top], s=120, marker='D', label='Ponto próximo de (0.01, 0.01)')

    ax.set_xlim(-0.0002, L + 0.0002)
    ax.set_ylim(-0.0002, H + 0.0005)
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_title('Malha ')
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig('graficos/malha_node_centered_semivolumes.png', dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================
# 7) FUNÇÃO PARA SALVAR O CAMPO DE TEMPERATURA EM UM INSTANTE
# ============================================================
def save_temperature_field(T_field, t, file_prefix='temperatura_node_centered'):
    """
    Salva um gráfico do campo de temperatura em um instante t.
    Como a malha é node-centered, usamos os nós diretamente.
    """
    X, Y = np.meshgrid(x_nodes, y_nodes)

    plt.figure(figsize=(8, 4))
    cp = plt.contourf(X, Y, T_field, levels=20)
    plt.colorbar(cp, label='Temperatura (°C)')
    plt.scatter(X, Y, s=8)
    plt.xlabel('x (m)')
    plt.ylabel('y (m)')
    plt.title(f'Distribuição de temperatura em t = {t:.1f} s (node-centered)')
    plt.tight_layout()
    plt.savefig(f'graficos/{file_prefix}_t_{t:05.1f}s.png', dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================
# 8) MONTAGEM DA MATRIZ DO SISTEMA IMPLÍCITO NODE-CENTERED
# ============================================================
def build_system_node_centered(T_old):
    """
    Monta o sistema linear A*T_new = b para um passo de tempo.

    Nesta formulação node-centered:
    - a incógnita está nos nós;
    - o volume de controle ao redor de cada nó pode ser inteiro,
      meio volume ou quarto de volume;
    - nós internos trocam calor por condução com os vizinhos;
    - nós de contorno recebem contribuições de convecção/fluxo diretamente
      nas faces do seu volume de controle.
    """
    N = Nx * Ny
    A = lil_matrix((N, N), dtype=float)
    b = np.zeros(N, dtype=float)

    for j in range(Ny):
        for i in range(Nx):
            p = idx(i, j)

            # Dimensões do volume de controle do nó P
            width_cv = cv_width(i)
            height_cv = cv_height(j)
            Vp = width_cv * height_cv * depth

            # Áreas das faces do volume de controle
            # faces leste/oeste: altura do CV
            Ae = height_cv * depth
            Aw = height_cv * depth
            # faces norte/sul: largura do CV
            An = width_cv * depth
            As = width_cv * depth

            # Termo transiente
            aP0_local = rho_cp * Vp / dt
            aP = aP0_local
            rhs = aP0_local * T_old[j, i]

            # ----------------------------------------------------
            # LESTE
            # ----------------------------------------------------
            if i < Nx - 1:
                # Vizinho leste existe -> condução com nó vizinho
                aE = k * Ae / dx
                A[p, idx(i + 1, j)] = -aE
                aP += aE
            else:
                # Borda leste -> convecção direta na face leste
                aP += h * Ae
                rhs += h * Ae * T_inf

            # ----------------------------------------------------
            # OESTE
            # ----------------------------------------------------
            if i > 0:
                aW = k * Aw / dx
                A[p, idx(i - 1, j)] = -aW
                aP += aW
            else:
                # Borda oeste -> convecção
                aP += h * Aw
                rhs += h * Aw * T_inf

            # ----------------------------------------------------
            # NORTE
            # ----------------------------------------------------
            if j < Ny - 1:
                aN = k * An / dy
                A[p, idx(i, j + 1)] = -aN
                aP += aN
            else:
                # Borda superior -> convecção
                aP += h * An
                rhs += h * An * T_inf

            # ----------------------------------------------------
            # SUL
            # ----------------------------------------------------
            if j > 0:
                aS = k * As / dy
                A[p, idx(i, j - 1)] = -aS
                aP += aS
            else:
                # Borda inferior y = 0
                xP = x_nodes[i]

                if is_heat_flux_region(xP):
                    # Fluxo imposto entrando no volume de controle
                    rhs += q_flux * As
                else:
                    # Região não aquecida -> convecção com o ambiente
                    aP += h * As
                    rhs += h * As * T_inf

            # Coeficiente central
            A[p, p] = aP
            b[p] = rhs

    return csr_matrix(A), b


# ============================================================
# 9) DESENHA A MALHA ANTES DE INICIAR A SIMULAÇÃO
# ============================================================
plot_node_centered_mesh()


# ============================================================
# 10) MARCHA NO TEMPO
# ============================================================
# Para evitar salvar o mesmo instante mais de uma vez por efeito numérico,
# guardamos os tempos já salvos.
saved_times = set()

for n in range(nt + 1):
    t = n * dt

    # Guarda histórico nos três pontos pedidos
    time_history.append(t)
    T_bottom_history.append(T[j_probe_bottom, i_probe])
    T_mid_history.append(T[j_probe_mid, i_probe])
    T_top_history.append(T[j_probe_top, i_probe])

    # Salva mapas de temperatura em instantes escolhidos (0, 12, 24, ...)
    for ts in save_times:
        if abs(t - ts) <= 0.5 * dt and ts not in saved_times:
            save_temperature_field(T, ts)
            saved_times.add(ts)

    # Último instante: não precisa avançar
    if n == nt:
        break

    # Monta e resolve o sistema implícito
    A, b = build_system_node_centered(T)
    T_new_flat = spsolve(A, b)

    # Volta para a forma 2D
    T = T_new_flat.reshape((Ny, Nx))


# ============================================================
# 11) GRÁFICO DO CAMPO FINAL
# ============================================================
Xn, Yn = np.meshgrid(x_nodes, y_nodes)

plt.figure(figsize=(8, 4))
cp = plt.contourf(Xn, Yn, T, levels=20)
plt.colorbar(cp, label='Temperatura (°C)')
plt.scatter(Xn, Yn, s=8)
plt.xlabel('x (m)')
plt.ylabel('y (m)')
plt.title(f'Distribuição de temperatura em t = {t_final:.1f} s (node-centered)')
plt.tight_layout()
plt.savefig('graficos/temperatura_final_node_centered.png', dpi=300, bbox_inches='tight')
plt.close()


# ============================================================
# 12) GRÁFICO DO HISTÓRICO TEMPORAL
# ============================================================
plt.figure(figsize=(8, 5))
plt.plot(time_history, T_bottom_history, label='T(x≈0.01, y≈0, t)')
plt.plot(time_history, T_mid_history, label='T(x≈0.01, y≈0.005, t)')
plt.plot(time_history, T_top_history, label='T(x≈0.01, y≈0.01, t)')
plt.xlabel('Tempo (s)')
plt.ylabel('Temperatura (°C)')
plt.title('Histórico de temperatura (malha node-centered)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('graficos/historico_temperatura_node_centered.png', dpi=300, bbox_inches='tight')
plt.close()

print('Simulação node-centered concluída.')
print("Gráficos salvos na pasta 'graficos'.")
