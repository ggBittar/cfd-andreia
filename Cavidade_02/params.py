from dataclasses import dataclass, field
import numpy as np


@dataclass
class CavityConfig:
    nx: int = 129
    ny: int = 129
    lx: float = 1.0
    ly: float = 1.0
    rho: float = 1000
    Re: float = 100.0
    u_max: float = 1.0
    t_ini: float = 0.0
    t_final: float = 10
    CFL: float = 0.1
    sor_w: float = 1.85
    sor_tolerance: float = 1.0e-5
    sor_max_iter: int = 800
    mass_tolerance: float = 1.0e-3
    stop_by_convergence: bool = True
    convergence_tolerance: float = 1.0e-4
    min_steps_before_convergence: int = 10
    max_steps: int = 50000
    report_interval: int = 5
    plot_results: bool = False
    plot_results_2: bool = True
    plot_profiles: bool = True
    plot_ghia_reference: bool = True
    plot_mesh: bool = False
    dx: float = field(init=False)
    dy: float = field(init=False)
    nu: float = field(init=False)
    dt: float = field(init=False)

    def __post_init__(self):
        if self.nx < 3 or self.ny < 3:
            raise ValueError("nx e ny devem ser maiores ou iguais a 3.")
        self.dx = self.lx / (self.nx - 1)
        self.dy = self.ly / (self.ny - 1)
        self.nu = self.u_max * self.ly / self.Re
        advective_dt = self.CFL * min(self.dx, self.dy) / max(abs(self.u_max), 1.0e-12)
        diffusive_dt = 0.25 * min(self.dx, self.dy) ** 2 / max(self.nu, 1.0e-12)
        self.dt = min(advective_dt, diffusive_dt)

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
    u: np.ndarray
    v: np.ndarray
    P: np.ndarray


def criar_condicoes_iniciais(config: CavityConfig) -> InitialConditions:
    shape = (config.ny + 2, config.nx + 2)
    return InitialConditions(
        u=np.zeros(shape, dtype=float),
        v=np.zeros(shape, dtype=float),
        P=np.zeros(shape, dtype=float),
    )
    
