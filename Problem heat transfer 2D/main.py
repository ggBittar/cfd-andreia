import numpy as np
import matplotlib.pyplot as plt
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
import os

# ============================================================
# 1) DADOS DO PROBLEMA
# ============================================================
# Dados do enunciado:
# largura da chapa: L = 0.02 m
# espessura/altura da chapa: e = 0.01 m
# temperatura inicial: 30 °C
# temperatura ambiente: 30 °C
# coeficiente convectivo: h = 20 W/m²K
# fluxo de calor imposto em duas regiões da base: q'' = 5e4 W/m²
# condutividade térmica: k = 14.9 W/mK
# difusividade térmica: alpha = 3.95e-6 m²/s
# tempo final: 60 s

L = 0.02
H = 0.01
T_inf = 30.0
T0 = 30.0
h = 20.0
q_flux = 5.0e4
k = 14.9
alpha = 3.95e-6
t_final = 60.0

# A partir de alpha = k/(rho*cp), obtemos rho*cp
rho_cp = k / alpha


# ============================================================
# 2) MALHA NUMÉRICA
# ============================================================
# Você pode refinar se quiser.
Nx = 41
Ny = 21

dx = L / Nx
dy = H / Ny

# Coordenadas dos centros dos volumes
x_centers = (np.arange(Nx) + 0.5) * dx
y_centers = (np.arange(Ny) + 0.5) * dy

# Passo de tempo
dt = 0.1
nt = int(t_final / dt)

# Profundidade unitária da chapa (modelo 2D por unidade de profundidade)
depth = 1.0

# Áreas das faces
Ae = Aw = dy * depth
An = As = dx * depth

# Volume de um volume interno
V = dx * dy * depth

# Termo transiente
aP0 = rho_cp * V / dt


# ============================================================
# 3) FUNÇÕES AUXILIARES
# ============================================================
def idx(i, j):
    """
    Converte o índice 2D (i, j) em índice 1D para montar a matriz.
    i -> direção x
    j -> direção y
    """
    return j * Nx + i


def is_heat_flux_region(x):
    """
    Retorna True se a posição x estiver em uma das regiões da base
    onde o fluxo de calor é imposto.
    Regiões:
      0.003 <= x <= 0.008
      0.012 <= x <= 0.017
    """
    return (0.003 <= x <= 0.008) or (0.012 <= x <= 0.017)


def convection_conductance_half_cell(k, h, delta, area):
    """
    Condutância equivalente entre o centro do volume e o ambiente
    para uma fronteira convectiva usando MEIO VOLUME.

    Resistência total = condução (meia célula) + convecção
                      = (delta/2)/(k*A) + 1/(h*A)

    Logo:
      G = 1 / R_total
        = A / ((delta/(2*k)) + (1/h))
    """
    return area / (delta / (2.0 * k) + 1.0 / h)


# ============================================================
# 4) CONDIÇÃO INICIAL
# ============================================================
T = np.full((Ny, Nx), T0, dtype=float)

# Vamos armazenar histórico nas três posições pedidas:
# T(x = 0.01, y = 0, t)
# T(x = 0.01, y = 0.005, t)
# T(x = 0.01, y = 0.01, t)
#
# Como trabalhamos com centros dos volumes, usamos o centro mais próximo.

def nearest_i(x_target):
    return np.argmin(np.abs(x_centers - x_target))

def nearest_j(y_target):
    return np.argmin(np.abs(y_centers - y_target))

i_probe = nearest_i(0.01)
j_probe_bottom = nearest_j(0.0)
j_probe_mid = nearest_j(0.005)
j_probe_top = nearest_j(0.01)

time_history = []
T_bottom_history = []
T_mid_history = []
T_top_history = []

# ------------------------------------------------------------
# Configuração para salvar mapas do campo de temperatura
# em vários instantes de tempo.
#
# Exemplo: se save_field_interval = 12.0, o código salvará
# mapas em t = 0, 12, 24, 36, 48 e 60 s.
# ------------------------------------------------------------
save_field_interval = 12.0
snapshot_times = np.arange(0.0, t_final + 0.5 * save_field_interval, save_field_interval)
snapshots = {}


# ============================================================
# 5) MONTAGEM DA MATRIZ DO SISTEMA IMPLÍCITO
# ============================================================
def build_system(T_old):
    """
    Monta o sistema linear A*T_new = b do passo de tempo atual.

    T_old: campo de temperatura no tempo n
    retorna:
      A: matriz esparsa
      b: vetor do lado direito
    """
    N = Nx * Ny
    A = lil_matrix((N, N), dtype=float)
    b = np.zeros(N, dtype=float)

    for j in range(Ny):
        for i in range(Nx):
            p = idx(i, j)

            # Começamos com o termo transiente
            aP = aP0
            rhs = aP0 * T_old[j, i]

            # ====================================================
            # CONTRIBUIÇÃO LESTE
            # ====================================================
            if i < Nx - 1:
                # vizinho interno a leste
                aE = k * Ae / dx
                A[p, idx(i + 1, j)] = -aE
                aP += aE
            else:
                # fronteira leste com convecção
                G_e = convection_conductance_half_cell(k, h, dx, Ae)
                aP += G_e
                rhs += G_e * T_inf

            # ====================================================
            # CONTRIBUIÇÃO OESTE
            # ====================================================
            if i > 0:
                # vizinho interno a oeste
                aW = k * Aw / dx
                A[p, idx(i - 1, j)] = -aW
                aP += aW
            else:
                # fronteira oeste com convecção
                G_w = convection_conductance_half_cell(k, h, dx, Aw)
                aP += G_w
                rhs += G_w * T_inf

            # ====================================================
            # CONTRIBUIÇÃO NORTE
            # ====================================================
            if j < Ny - 1:
                # vizinho interno ao norte
                aN = k * An / dy
                A[p, idx(i, j + 1)] = -aN
                aP += aN
            else:
                # fronteira superior com convecção
                G_n = convection_conductance_half_cell(k, h, dy, An)
                aP += G_n
                rhs += G_n * T_inf

            # ====================================================
            # CONTRIBUIÇÃO SUL
            # ====================================================
            if j > 0:
                # vizinho interno ao sul
                aS = k * As / dy
                A[p, idx(i, j - 1)] = -aS
                aP += aS
            else:
                # fronteira inferior y = 0
                # Nesta borda, parte recebe fluxo imposto e parte convecção.
                xP = x_centers[i]

                if is_heat_flux_region(xP):
                    # fluxo de calor entrando na chapa
                    # entra diretamente como fonte no vetor rhs
                    rhs += q_flux * As
                else:
                    # região sem fluxo imposto -> convecção
                    G_s = convection_conductance_half_cell(k, h, dy, As)
                    aP += G_s
                    rhs += G_s * T_inf

            # coeficiente central
            A[p, p] = aP
            b[p] = rhs

    return csr_matrix(A), b


# ============================================================
# 6) MARCHA NO TEMPO
# ============================================================
for n in range(nt + 1):
    t = n * dt

    # Armazena histórico antes do próximo passo
    time_history.append(t)
    T_bottom_history.append(T[j_probe_bottom, i_probe])
    T_mid_history.append(T[j_probe_mid, i_probe])
    T_top_history.append(T[j_probe_top, i_probe])

    # --------------------------------------------------------
    # Se o tempo atual estiver próximo de um dos instantes de
    # salvamento, guarda uma cópia do campo de temperatura.
    #
    # Usamos uma tolerância de dt/2 para evitar problemas de
    # arredondamento numérico na comparação entre tempos.
    # --------------------------------------------------------
    for ts in snapshot_times:
        if abs(t - ts) <= 0.5 * dt and ts not in snapshots:
            snapshots[float(ts)] = T.copy()

    # Último instante não precisa avançar
    if n == nt:
        break

    # Monta e resolve sistema
    A, b = build_system(T)
    T_new_flat = spsolve(A, b)

    # Converte de volta para matriz 2D
    T = T_new_flat.reshape((Ny, Nx))


# ============================================================
# 7) VISUALIZAÇÃO DA MALHA DE VOLUMES FINITOS
# ============================================================
# Nesta etapa vamos gerar uma figura apenas da malha numérica.
# A ideia é enxergar:
#   1) as linhas que delimitam cada volume de controle
#   2) os centros dos volumes, onde a temperatura T(i,j) é armazenada
#   3) as duas regiões da base que recebem fluxo de calor imposto
#
# Isso ajuda bastante a entender o método dos volumes finitos,
# porque a variável não fica armazenada no nó da grade, e sim no
# CENTRO de cada volume.

# Coordenadas das linhas da malha (fronteiras dos volumes)
x_faces = np.linspace(0.0, L, Nx + 1)
y_faces = np.linspace(0.0, H, Ny + 1)

# Cria a pasta "graficos" se ela não existir
os.makedirs("graficos", exist_ok=True)

# ----------------------------
# gráfico da malha numérica
# ----------------------------
plt.figure(figsize=(10, 5))

# Desenha as linhas verticais da malha
for xf in x_faces:
    plt.plot([xf, xf], [0.0, H], color='black', linewidth=0.8)

# Desenha as linhas horizontais da malha
for yf in y_faces:
    plt.plot([0.0, L], [yf, yf], color='black', linewidth=0.8)

# Desenha os centros dos volumes de controle
Xc, Yc = np.meshgrid(x_centers, y_centers)
plt.scatter(Xc, Yc, s=18, marker='o', label='Centros dos volumes')

# Marca as duas regiões da base com fluxo imposto
# Região 1: 0.003 <= x <= 0.008, em y = 0
# Região 2: 0.012 <= x <= 0.017, em y = 0
plt.plot([0.003, 0.008], [0.0, 0.0], linewidth=5, solid_capstyle='butt',
         label='Fluxo de calor imposto')
plt.plot([0.012, 0.017], [0.0, 0.0], linewidth=5, solid_capstyle='butt')

# Destaca os três pontos de acompanhamento de temperatura
plt.scatter([x_centers[i_probe]], [y_centers[j_probe_bottom]], s=70, marker='s',
            label='Ponto próximo de (0.01, 0)')
plt.scatter([x_centers[i_probe]], [y_centers[j_probe_mid]], s=70, marker='^',
            label='Ponto próximo de (0.01, 0.005)')
plt.scatter([x_centers[i_probe]], [y_centers[j_probe_top]], s=70, marker='D',
            label='Ponto próximo de (0.01, 0.01)')

plt.xlabel('x (m)')
plt.ylabel('y (m)')
plt.title('Malha de volumes finitos e centros dos elementos')
plt.xlim(0.0, L)
plt.ylim(0.0, H)
plt.gca().set_aspect('equal')
plt.grid(False)
plt.legend(loc='upper right', fontsize=8)
plt.tight_layout()
plt.savefig("graficos/malha_volumes_finitos.png", dpi=300, bbox_inches="tight")
plt.close()

# ============================================================
# 8) SALVAR GRÁFICOS EM UMA PASTA
# ============================================================

X, Y = np.meshgrid(x_centers, y_centers)

# ----------------------------
# gráfico do campo de temperatura final
# ----------------------------
plt.figure(figsize=(8, 4))
cp = plt.contourf(X, Y, T, levels=20)
plt.colorbar(cp, label='Temperatura (°C)')
plt.xlabel('x (m)')
plt.ylabel('y (m)')
plt.title(f'Distribuição de temperatura em t = {t_final:.1f} s')
plt.tight_layout()
plt.savefig("graficos/temperatura_final.png", dpi=300, bbox_inches="tight")
plt.close()

# ----------------------------
# gráficos do campo de temperatura em vários instantes
# ----------------------------
# Cada snapshot salvo durante a simulação gera uma figura
# própria. O nome do arquivo inclui o tempo correspondente.
for ts in sorted(snapshots.keys()):
    T_snap = snapshots[ts]

    plt.figure(figsize=(8, 4))
    cp = plt.contourf(X, Y, T_snap, levels=20)
    plt.colorbar(cp, label='Temperatura (°C)')
    plt.xlabel('x (m)')
    plt.ylabel('y (m)')
    plt.title(f'Distribuição de temperatura em t = {ts:.1f} s')
    plt.tight_layout()
    plt.savefig(f"graficos/temperatura_t_{ts:05.1f}s.png", dpi=300, bbox_inches="tight")
    plt.close()

# ----------------------------
# gráfico do histórico de temperatura
# ----------------------------
plt.figure(figsize=(8, 5))
plt.plot(time_history, T_bottom_history, label='T(x=0.01, y=0, t)')
plt.plot(time_history, T_mid_history, label='T(x=0.01, y=0.005, t)')
plt.plot(time_history, T_top_history, label='T(x=0.01, y=0.01, t)')
plt.xlabel('Tempo (s)')
plt.ylabel('Temperatura (°C)')
plt.title('Histórico de temperatura')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("graficos/historico_temperatura.png", dpi=300, bbox_inches="tight")
plt.close()

print("Gráficos salvos na pasta 'graficos'")