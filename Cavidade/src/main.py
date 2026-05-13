from __future__ import annotations

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from latex_widget import LatexGuideWidget
from simulation_widget import SimulationWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cavidade com Tampa Deslizante — Discretização e Simulação")
        self.resize(1180, 760)
        tabs = QTabWidget()
        tabs.addTab(LatexGuideWidget(), "Discretização em LaTeX")
        tabs.addTab(SimulationWidget(), "Simulação temporal")
        self.setCentralWidget(tabs)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
