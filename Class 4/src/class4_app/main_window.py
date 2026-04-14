from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from .graph_widget import GraphWidget
from .latex_widget import LatexWidget
from .selector_widget import SelectorWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Class 4")
        self.resize(1120, 760)

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.latex_widget = LatexWidget(self)
        self.selector_widget = SelectorWidget(self)
        self.graph_widget = GraphWidget(self)

        self.tabs.addTab(self.latex_widget, "Formulacoes")
        self.tabs.addTab(self.selector_widget, "Parametros")
        self.tabs.addTab(self.graph_widget, "Grafico")

        self.selector_widget.configuration_changed.connect(self.graph_widget.set_configuration)
        self.selector_widget.apply_requested.connect(self._show_graph_tab)
        self.selector_widget.emit_configuration()

    def _show_graph_tab(self, *_args) -> None:
        self.tabs.setCurrentWidget(self.graph_widget)
