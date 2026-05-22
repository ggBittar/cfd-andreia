import numpy as np
import matplotlib.pyplot as plt

from params import CavityConfig, DiscretizationTypes, MeshType, MeshTypes
from malhas import gerar_malha, vizualizar_malha

config = CavityConfig()

mesh_type = MeshType(type=MeshTypes.DF)  # "C", "DF" ou "DB"
disc_type = DiscretizationTypes.C  # "A" para volume nulo, "B" para semi-volume, "C" para célula fantasma

X, Y = gerar_malha(config, disc_type)

vizualizar_malha(X, Y, mesh_type)

