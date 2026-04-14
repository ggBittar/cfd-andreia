import numpy as np
import matplotlib.pyplot as plt
from scipy.sparse import lil_matrix, csc_matrix
from scipy.sparse.linalg import spsolve

# ==========================================================
# DADOS DO PROBLEMA
# ==========================================================
Lx = 0.02         # comprimento em x [m]
Ly = 0.01         # espessura/altura em y [m]

k = 14.9          # condutividade térmica [W/m.K]
alpha = 3.95e-6   # difusividade térmica [m²/s]
h = 20.0          # coeficiente de convecção [W/m².K]
T_inf = 30.0      # temperatura ambiente [°C]
T0 = 30.0         # temperatura inicial [°C]
q_flux = 5e4      # fluxo de calor imposto [W/m²]

t_final = 60.0    # tempo final [s]
dt = 0.2          # passo de tempo [s]

# ==========================================================
# PROPRIEDADES COMPLEMENTARES
# alpha = k / (rho*cp) => rho*cp = k/alpha
# ==========================================================
rho_cp = k / alpha  # [J/m³.K]

# Espessura unitária na direção perpendicular ao plano
# (problema 2D por unidade de profundidade)
z = 1.0

# ==========================================================
# MALHA
# Escolha de malha contendo exatamente:
# x = 0.01
# y = 0.00, 0.005, 0.01
# ==========================================================
Nx = 41
Ny = 21

dx = Lx / Nx
dy = Ly / Ny

# centros dos volumes
x = np.linspace(dx/2, Lx - dx/2, Nx)
y = np.linspace(dy/2, Ly - dy/2, Ny)

# tempo
nt = int(t_final / dt)

# ==========================================================
# REGIÕES COM FLUXO DE CALOR NA FACE SUPERIOR (y = 0)
# 0.003 <= x <= 0.008
# 0.012 <= x <= 0.017
# ==========================================================
def top_boundary_flux(xc):
    if (0.003 <= xc <= 0.008) or (0.012 <= xc <= 0.017):
        return q_flux
    return None  # restante da borda superior sofre convecção

# ==========================================================
# INDEXAÇÃO 2D -> 1D
# ==========================================================
def idx(i, j):
    return j * Nx + i

N = Nx * Ny

# ==========================================================
# INICIALIZAÇÃO DO CAMPO
# ==========================================================
T = np.full((Ny, Nx), T0)

# ==========================================================
# PONTOS DE MONITORAMENTO PEDIDOS
# T(x=0.01,y=0,t), T(x=0.01,y=0.005,t), T(x=0.01,y=0.01,t)
#
# Como o método usa centros de volume, pegamos o centro mais próximo.
# ==========================================================
def nearest_index(arr, value):
    return np.argmin(np.abs(arr - value))

ix = nearest_index(x, 0.01)
jy_top = nearest_index(y, 0.0)
jy_mid = nearest_index(y, 0.005)
jy_bot = nearest_index(y, 0.01)

time_hist = [0.0]
T_top_hist = [T[jy_top, ix]]
T_mid_hist = [T[jy_mid, ix]]
T_bot_hist = [T[jy_bot, ix]]

# ==========================================================
# FUNÇÃO PARA MONTAR O SISTEMA LINEAR A*T_new = b
# COM COEFICIENTES CLÁSSICOS DE VOLUMES FINITOS
# ==========================================================
def assemble_system(T_old):
    A = lil_matrix((N, N))
    b = np.zeros(N)

    # áreas das faces
    Ae = Aw = dy * z
    An = As = dx * z

    # volume do controle
    V = dx * dy * z

    # termo transiente implícito
    aP0 = rho_cp * V / dt

    for j in range(Ny):
        for i in range(Nx):
            p = idx(i, j)

            # coeficientes de difusão padrão
            aE = 0.0
            aW = 0.0
            aN = 0.0
            aS = 0.0

            Su = 0.0
            Sp = 0.0

            # ----------------------------------------------
            # LESTE
            # ----------------------------------------------
            if i < Nx - 1:
                aE = k * Ae / dx
            else:
                # borda direita: convecção
                # tratamento por meia distância:
                # q = (T_P - T_inf) / [ (dx/2)/k + 1/h ]
                # equivalente a termo fonte linearizado
                R_cond = (dx / 2) / (k * Ae)
                R_conv = 1 / (h * Ae)
                U = 1 / (R_cond + R_conv)
                Sp -= U
                Su += U * T_inf

            # ----------------------------------------------
            # OESTE
            # ----------------------------------------------
            if i > 0:
                aW = k * Aw / dx
            else:
                # borda esquerda: convecção
                R_cond = (dx / 2) / (k * Aw)
                R_conv = 1 / (h * Aw)
                U = 1 / (R_cond + R_conv)
                Sp -= U
                Su += U * T_inf

            # ----------------------------------------------
            # NORTE
            # Aqui j=0 é a borda superior do desenho/enunciado
            # ----------------------------------------------
            if j > 0:
                aN = k * An / dy
            else:
                qtop = top_boundary_flux(x[i])

                if qtop is not None:
                    # fluxo imposto na face superior
                    # entra como fonte no volume:
                    # Su += q'' * A_face
                    Su += qtop * An
                else:
                    # convecção na parte restante da face superior
                    R_cond = (dy / 2) / (k * An)
                    R_conv = 1 / (h * An)
                    U = 1 / (R_cond + R_conv)
                    Sp -= U
                    Su += U * T_inf

            # ----------------------------------------------
            # SUL
            # ----------------------------------------------
            if j < Ny - 1:
                aS = k * As / dy
            else:
                # borda inferior: convecção
                R_cond = (dy / 2) / (k * As)
                R_conv = 1 / (h * As)
                U = 1 / (R_cond + R_conv)
                Sp -= U
                Su += U * T_inf

            # ----------------------------------------------
            # COEFICIENTE CENTRAL
            # aP = aE + aW + aN + aS + aP0 - Sp
            # ----------------------------------------------
            aP = aE + aW + aN + aS + aP0 - Sp

            A[p, p] = aP

            if i < Nx - 1:
                A[p, idx(i + 1, j)] = -aE
            if i > 0:
                A[p, idx(i - 1, j)] = -aW
            if j > 0:
                A[p, idx(i, j - 1)] = -aN
            if j < Ny - 1:
                A[p, idx(i, j + 1)] = -aS

            b[p] = aP0 * T_old[j, i] + Su

    return csc_matrix(A), b

# ==========================================================
# SOLUÇÃO TRANSIENTE
# ==========================================================
snapshot_times = [1, 5, 10, 30, 60]
snapshots = {}

for n in range(1, nt + 1):
    t = n * dt

    A, b = assemble_system(T)
    T_vec = spsolve(A, b)
    T = T_vec.reshape((Ny, Nx))

    time_hist.append(t)
    T_top_hist.append(T[jy_top, ix])
    T_mid_hist.append(T[jy_mid, ix])
    T_bot_hist.append(T[jy_bot, ix])

    for ts in snapshot_times:
        if abs(t - ts) < dt / 2:
            snapshots[ts] = T.copy()

# ==========================================================
# RESULTADOS NUMÉRICOS
# ==========================================================
print("Temperaturas finais aproximadas:")
print(f"T(x=0.01, y=0.00, t=60s)  ≈ {T[jy_top, ix]:.4f} °C")
print(f"T(x=0.01, y=0.005, t=60s) ≈ {T[jy_mid, ix]:.4f} °C")
print(f"T(x=0.01, y=0.01, t=60s)  ≈ {T[jy_bot, ix]:.4f} °C")

# ==========================================================
# GRÁFICO T x t
# ==========================================================
plt.figure(figsize=(8, 5))
plt.plot(time_hist, T_top_hist, label='T(x=0.01, y=0.00, t)')
plt.plot(time_hist, T_mid_hist, label='T(x=0.01, y=0.005, t)')
plt.plot(time_hist, T_bot_hist, label='T(x=0.01, y=0.01, t)')
plt.xlabel('Tempo [s]')
plt.ylabel('Temperatura [°C]')
plt.title('Evolução temporal da temperatura')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# ==========================================================
# CAMPO FINAL DE TEMPERATURA
# ==========================================================
X, Y = np.meshgrid(x, y)

plt.figure(figsize=(8, 4))
cont = plt.contourf(X, Y, T, levels=30)
plt.colorbar(cont, label='Temperatura [°C]')
plt.xlabel('x [m]')
plt.ylabel('y [m]')
plt.title('Distribuição de temperatura em t = 60 s')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

# ==========================================================
# SNAPSHOTS OPCIONAIS
# ==========================================================
for ts in snapshot_times:
    if ts in snapshots:
        plt.figure(figsize=(8, 4))
        cont = plt.contourf(X, Y, snapshots[ts], levels=30)
        plt.colorbar(cont, label='Temperatura [°C]')
        plt.xlabel('x [m]')
        plt.ylabel('y [m]')
        plt.title(f'Distribuição de temperatura em t = {ts} s')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.show()