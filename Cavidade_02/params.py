from dataclasses import dataclass, field
import numpy as np


@dataclass
class CavityConfig:
    nx : int = 4
    ny : int = 4
    lx : float = 1.0
    ly : float = 1.0
    dx : float = lx/(nx-1)
    dy : float = ly/(ny-1)
    rho: float = 1000
    Re: float = 100.0
    u_max: float = 1.0
    nu: float = u_max*ly/Re
    t_ini: float = 0.0
    t_final: float = 10.0
    CFL: float = 0.1
    dt:float = CFL*min(dx, dy)
    w: float = 1.5

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
    
@dataclass
class InitialConditions:
    u: np.ndarray = field(default_factory=lambda: np.zeros((CavityConfig.ny+2, CavityConfig.nx+2)))
    v: np.ndarray = field(default_factory=lambda: np.zeros((CavityConfig.ny+2, CavityConfig.nx+2)))
    P: np.ndarray = field(default_factory=lambda: np.zeros((CavityConfig.ny+2, CavityConfig.nx+2)))
    
