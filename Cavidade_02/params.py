from dataclasses import dataclass
import numpy as np


@dataclass
class CavityConfig:
    nx : int = 4
    ny : int = 4
    lx : float = 1.0
    ly : float = 1.0
    lid_velocity : float = 1.0
    reynolds : float = 100.0
    dt : float | None = None
    poisson_iterations : int = 80
    poisson_tolerance : float = 1.0e-6

class MeshTypes:
    CL  = "Colocalizada"
    DF  = "Deslocada para frente"
    DB  = "Deslocada para trás"

@dataclass
class MeshType:
    type : str | None = None
    
class DiscretizationTypes:
    A = "Volume Nulo"
    B = "Semi-volume"
    C = "Célula Fantasma"