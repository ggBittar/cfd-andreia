from __future__ import annotations

import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox,
    QDoubleSpinBox, QComboBox, QMessageBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from cavity_solver import CavityConfig, LidDrivenCavitySolver


class SimulationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.solver = LidDrivenCavitySolver(CavityConfig())
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)

        self.figure = Figure(figsize=(7, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.start_button = QPushButton("Iniciar")
        self.pause_button = QPushButton("Pausar")
        self.reset_button = QPushButton("Resetar")
        self.step_button = QPushButton("Avançar 20 passos")

        self.re_box = QDoubleSpinBox()
        self.re_box.setRange(1.0, 5000.0)
        self.re_box.setValue(100.0)
        self.re_box.setDecimals(1)
        self.re_box.setSingleStep(50.0)

        self.n_box = QSpinBox()
        self.n_box.setRange(21, 121)
        self.n_box.setValue(41)
        self.n_box.setSingleStep(10)

        self.steps_box = QSpinBox()
        self.steps_box.setRange(1, 200)
        self.steps_box.setValue(5)

        self.plot_mode = QComboBox()
        self.plot_mode.addItems(["Velocidade |V|", "Vorticidade", "Função de corrente"])

        self.info_label = QLabel()

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Re:"))
        controls.addWidget(self.re_box)
        controls.addWidget(QLabel("Nós N×N:"))
        controls.addWidget(self.n_box)
        controls.addWidget(QLabel("Passos/tick:"))
        controls.addWidget(self.steps_box)
        controls.addWidget(QLabel("Campo:"))
        controls.addWidget(self.plot_mode)
        controls.addWidget(self.start_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.step_button)
        controls.addWidget(self.reset_button)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.canvas)
        layout.addWidget(self.info_label)

        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        self.reset_button.clicked.connect(self.reset)
        self.step_button.clicked.connect(lambda: self.advance(force_steps=20))
        self.plot_mode.currentIndexChanged.connect(self.update_plot)

        self.update_plot()

    def start(self):
        self.timer.start(40)

    def pause(self):
        self.timer.stop()

    def reset(self):
        self.pause()
        n = int(self.n_box.value())
        re = float(self.re_box.value())
        try:
            self.solver.reset(reynolds=re, nx=n, ny=n)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao resetar", str(exc))
        self.update_plot()

    def advance(self, force_steps: int | None = None):
        try:
            self.solver.step(force_steps or int(self.steps_box.value()))
        except Exception as exc:
            self.pause()
            QMessageBox.critical(self, "Simulação interrompida", str(exc))
        self.update_plot()

    def field_for_plot(self):
        mode = self.plot_mode.currentText()
        if mode == "Vorticidade":
            return self.solver.omega, "Vorticidade ω"
        if mode == "Função de corrente":
            return self.solver.psi, "Função de corrente ψ"
        speed = np.sqrt(self.solver.u**2 + self.solver.v**2)
        return speed, "Módulo da velocidade |V|"

    def update_plot(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        field, title = self.field_for_plot()
        x = self.solver.x
        y = self.solver.y
        extent = [x.min(), x.max(), y.min(), y.max()]
        im = self.ax.imshow(field, origin="lower", extent=extent, aspect="equal")
        # Linhas de corrente ficam úteis quando o campo já evoluiu um pouco.
        if self.solver.iteration > 10:
            xs, ys = np.meshgrid(x, y)
            stride = max(1, len(x) // 30)
            self.ax.streamplot(
                xs[::stride, ::stride], ys[::stride, ::stride],
                self.solver.u[::stride, ::stride], self.solver.v[::stride, ::stride],
                density=1.1, linewidth=0.7, arrowsize=0.8
            )
        self.ax.set_title(title)
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_xlim(0, self.solver.cfg.lx)
        self.ax.set_ylim(0, self.solver.cfg.ly)
        self.figure.colorbar(im, ax=self.ax, fraction=0.046, pad=0.04)
        self.info_label.setText(
            f"Iteração: {self.solver.iteration} | tempo: {self.solver.time:.4f} s | "
            f"dt: {self.solver.dt:.3e} | Re: {self.solver.reynolds:.1f} | "
            f"ν: {self.solver.nu:.3e}"
        )
        self.canvas.draw_idle()
