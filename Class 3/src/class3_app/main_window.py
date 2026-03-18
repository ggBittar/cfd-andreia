from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from .function_selector import FunctionSelector
from .graph_widget import GraphWidget
from .latex_widget import LatexWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Class 3")
        self.resize(1120, 760)

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.latex_widget = LatexWidget(self)
        self.function_selector = FunctionSelector(self)
        self.graph_widget = GraphWidget(self)

        self.tabs.addTab(self.latex_widget, "Formulacoes")
        self.tabs.addTab(self.function_selector, "Parametros")
        self.tabs.addTab(self.graph_widget, "Grafico")

        self.function_selector.definition_changed.connect(self.graph_widget.set_plot_definition)
        self.function_selector.definition_changed.connect(self._show_graph_tab)
        self.function_selector.emit_selection()

    def _show_graph_tab(self, *_args) -> None:
        self.tabs.setCurrentWidget(self.graph_widget)
