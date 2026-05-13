"""Solver 2D para cavidade com tampa deslizante.

Formulação: Navier-Stokes incompressível em vorticidade-função de corrente.
Discretização: malha node-centered, diferenças finitas equivalentes a volumes finitos
centrados nos nós. Nas bordas, os volumes de controle são semi-volumes.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class CavityConfig:
    nx: int = 41
    ny: int = 41
    lx: float = 1.0
    ly: float = 1.0
    lid_velocity: float = 1.0
    reynolds: float = 100.0
    dt: float | None = None
    poisson_iterations: int = 80
    poisson_tolerance: float = 1.0e-6


class LidDrivenCavitySolver:
    """Simulador explícito para cavidade quadrada com tampa móvel.

    O domínio é [0,Lx] x [0,Ly], com u=U na tampa superior e paredes sem escorregamento.
    A condição de contorno da vorticidade usa a aproximação de Thom, consistente
    com semi-volumes na fronteira e com a função de corrente constante nas paredes.
    """

    def __init__(self, config: CavityConfig):
        self.cfg = config
        self.nx = int(config.nx)
        self.ny = int(config.ny)
        if self.nx < 11 or self.ny < 11:
            raise ValueError("Use ao menos 11 nós em cada direção.")

        self.x = np.linspace(0.0, config.lx, self.nx)
        self.y = np.linspace(0.0, config.ly, self.ny)
        self.dx = config.lx / (self.nx - 1)
        self.dy = config.ly / (self.ny - 1)
        self.U = float(config.lid_velocity)
        self.nu = self.U * config.lx / float(config.reynolds)

        if config.dt is None:
            adv = 0.45 * min(self.dx, self.dy) / max(abs(self.U), 1.0e-12)
            diff = 0.20 * min(self.dx, self.dy) ** 2 / max(self.nu, 1.0e-12)
            self.dt = min(adv, diff)
        else:
            self.dt = float(config.dt)

        self.psi = np.zeros((self.ny, self.nx), dtype=float)
        self.omega = np.zeros_like(self.psi)
        self.u = np.zeros_like(self.psi)
        self.v = np.zeros_like(self.psi)
        self.time = 0.0
        self.iteration = 0
        self.apply_boundary_conditions()

    @property
    def reynolds(self) -> float:
        return self.U * self.cfg.lx / self.nu

    def reset(self, reynolds: float | None = None, nx: int | None = None, ny: int | None = None) -> None:
        cfg = CavityConfig(
            nx=nx or self.cfg.nx,
            ny=ny or self.cfg.ny,
            lx=self.cfg.lx,
            ly=self.cfg.ly,
            lid_velocity=self.cfg.lid_velocity,
            reynolds=reynolds or self.cfg.reynolds,
            dt=self.cfg.dt,
            poisson_iterations=self.cfg.poisson_iterations,
            poisson_tolerance=self.cfg.poisson_tolerance,
        )
        self.__init__(cfg)

    def apply_boundary_conditions(self) -> None:
        """Aplica velocidades de parede e vorticidade de fronteira.

        Índices: matriz [j, i], j vertical. A tampa está em j = ny-1.
        """
        # Função de corrente constante em todas as paredes impermeáveis.
        self.psi[0, :] = 0.0
        self.psi[-1, :] = 0.0
        self.psi[:, 0] = 0.0
        self.psi[:, -1] = 0.0

        # Velocidades nas paredes. Não se zera o interior aqui, pois ele é
        # calculado a partir de psi em update_velocity_from_streamfunction().
        self.u[-1, :] = self.U
        self.v[-1, :] = 0.0
        self.u[0, :] = 0.0
        self.v[0, :] = 0.0
        self.u[:, 0] = 0.0
        self.v[:, 0] = 0.0
        self.u[:, -1] = 0.0
        self.v[:, -1] = 0.0

        # Vorticidade de Thom nas paredes.
        self.omega[0, 1:-1] = -2.0 * self.psi[1, 1:-1] / self.dy**2
        self.omega[-1, 1:-1] = -2.0 * self.psi[-2, 1:-1] / self.dy**2 - 2.0 * self.U / self.dy
        self.omega[1:-1, 0] = -2.0 * self.psi[1:-1, 1] / self.dx**2
        self.omega[1:-1, -1] = -2.0 * self.psi[1:-1, -2] / self.dx**2

        # Cantos: média das paredes adjacentes para evitar singularidade numérica.
        self.omega[0, 0] = 0.5 * (self.omega[0, 1] + self.omega[1, 0])
        self.omega[0, -1] = 0.5 * (self.omega[0, -2] + self.omega[1, -1])
        self.omega[-1, 0] = 0.5 * (self.omega[-1, 1] + self.omega[-2, 0])
        self.omega[-1, -1] = 0.5 * (self.omega[-1, -2] + self.omega[-2, -1])

    def solve_streamfunction(self) -> None:
        """Resolve ∇²ψ = -ω por Jacobi vetorizado."""
        dx2 = self.dx * self.dx
        dy2 = self.dy * self.dy
        denom = 2.0 * (dx2 + dy2)

        psi = self.psi
        for _ in range(self.cfg.poisson_iterations):
            old = psi.copy()
            psi[1:-1, 1:-1] = (
                dy2 * (old[1:-1, 2:] + old[1:-1, :-2])
                + dx2 * (old[2:, 1:-1] + old[:-2, 1:-1])
                + dx2 * dy2 * self.omega[1:-1, 1:-1]
            ) / denom
            psi[0, :] = psi[-1, :] = 0.0
            psi[:, 0] = psi[:, -1] = 0.0
            if np.max(np.abs(psi - old)) < self.cfg.poisson_tolerance:
                break

    def update_velocity_from_streamfunction(self) -> None:
        self.u[1:-1, 1:-1] = (self.psi[2:, 1:-1] - self.psi[:-2, 1:-1]) / (2.0 * self.dy)
        self.v[1:-1, 1:-1] = -(self.psi[1:-1, 2:] - self.psi[1:-1, :-2]) / (2.0 * self.dx)
        # Reimpõe paredes.
        self.u[0, :] = 0.0
        self.v[0, :] = 0.0
        self.u[-1, :] = self.U
        self.v[-1, :] = 0.0
        self.u[:, 0] = 0.0
        self.v[:, 0] = 0.0
        self.u[:, -1] = 0.0
        self.v[:, -1] = 0.0

    def convective_derivative_upwind(self, field: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Derivadas convectivas de primeira ordem por upwind."""
        dfdx_back = (field[1:-1, 1:-1] - field[1:-1, :-2]) / self.dx
        dfdx_forw = (field[1:-1, 2:] - field[1:-1, 1:-1]) / self.dx
        dfdy_back = (field[1:-1, 1:-1] - field[:-2, 1:-1]) / self.dy
        dfdy_forw = (field[2:, 1:-1] - field[1:-1, 1:-1]) / self.dy
        dudx = np.where(self.u[1:-1, 1:-1] >= 0.0, dfdx_back, dfdx_forw)
        dudy = np.where(self.v[1:-1, 1:-1] >= 0.0, dfdy_back, dfdy_forw)
        return dudx, dudy

    def step(self, nsteps: int = 1) -> None:
        for _ in range(nsteps):
            self.solve_streamfunction()
            self.update_velocity_from_streamfunction()
            self.apply_boundary_conditions()

            omega_old = self.omega.copy()
            domega_dx, domega_dy = self.convective_derivative_upwind(omega_old)
            lap = (
                (omega_old[1:-1, 2:] - 2.0 * omega_old[1:-1, 1:-1] + omega_old[1:-1, :-2]) / self.dx**2
                + (omega_old[2:, 1:-1] - 2.0 * omega_old[1:-1, 1:-1] + omega_old[:-2, 1:-1]) / self.dy**2
            )
            convection = self.u[1:-1, 1:-1] * domega_dx + self.v[1:-1, 1:-1] * domega_dy
            self.omega[1:-1, 1:-1] = omega_old[1:-1, 1:-1] + self.dt * (-convection + self.nu * lap)

            # Segurança contra instabilidades muito fortes em parâmetros agressivos.
            if not np.all(np.isfinite(self.omega)):
                raise FloatingPointError("A solução divergiu. Reduza dt, Re ou aumente a malha gradualmente.")

            self.time += self.dt
            self.iteration += 1
            self.apply_boundary_conditions()
