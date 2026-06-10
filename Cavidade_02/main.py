import numpy as np
import matplotlib.pyplot as plt

from params import CavityConfig, DiscretizationTypes, MeshType, MeshTypes, InitialConditions
from malhas import gerar_malha, vizualizar_malha, plotar_malha

config = CavityConfig()
initial_conditions = InitialConditions()

mesh_type = MeshType(type=MeshTypes.DF)  # "C", "DF" ou "DB"
disc_type = DiscretizationTypes.C  # "A" para volume nulo, "B" para semi-volume, "C" para célula fantasma

x, y = gerar_malha(config, disc_type)



vizualizar_malha(x, y, mesh_type)

X, Y = np.meshgrid(x, y)
print("Configurações da Cavidade:")
print(f"  - Dimensões: {config.nx} x {config.ny}")
print(f"  - Domínio: [{config.lx}, {config.ly}]")
print(f"  - Viscosidade cinemática: {config.nu}")
print(f"  - Número de Reynolds: {config.Re}")
print(f"  - Passo de tempo: {config.dt}")
print(f" - dx: {config.dx}, dy: {config.dy}")
print(f"  - Condições iniciais: u={initial_conditions.u}, v={initial_conditions.v}, P={initial_conditions.P}")

from solver import boundary_conditions

boundary_conditions(initial_conditions.u, initial_conditions.v, initial_conditions.P, config.u_max)

print(f"  - Condições iniciais: u={initial_conditions.u}, v={initial_conditions.v}, P={initial_conditions.P}")

from plotador import plotar_campo_velocidade

fig, ax = plotar_campo_velocidade(X, Y, initial_conditions.u, initial_conditions.v)

plotar_malha(ax, np.meshgrid(x, y), color="tab:blue", label="Pontos da Malha", linestyle="-", size=20)


