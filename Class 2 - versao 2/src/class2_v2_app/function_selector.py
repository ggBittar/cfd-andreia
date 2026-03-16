from __future__ import annotations

import re

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .function_catalog import available_functions, find_function_by_id
from .time_method_catalog import available_time_methods, find_time_method_by_id


def parse_int_values(text: str) -> list[int]:
    values: list[int] = []
    for part in re.split(r"[,;\s]+", text.strip()):
        if not part:
            continue
        try:
            values.append(int(part))
        except ValueError:
            continue
    return values


class FunctionSelector(QWidget):
    function_selected = pyqtSignal(object, float, float, float, int, object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.function_combo_box = QComboBox(self)
        self.x_min_input = QLineEdit(self)
        self.x_max_input = QLineEdit(self)
        self.tf_input = QLineEdit(self)
        self.n_input = QLineEdit(self)
        self.time_steps_input = QLineEdit(self)
        self.status_label = QLabel(self)
        self.method_checkboxes: list[QCheckBox] = []

        layout = QVBoxLayout(self)

        title = QLabel(
            "Selecione a formulacao em funcao de Phi, o dominio em x, o tempo final tf, um N de referencia, o vetor de passos Nt e os metodos temporais:",
            self,
        )
        title.setWordWrap(True)
        layout.addWidget(title)

        layout.addWidget(QLabel("Funcao:", self))
        for function in available_functions():
            self.function_combo_box.addItem(function.label, function.identifier)
        layout.addWidget(self.function_combo_box)

        layout.addWidget(QLabel("Dominio de x:", self))
        domain_layout = QHBoxLayout()
        self.x_min_input.setPlaceholderText("xmin")
        self.x_min_input.setText("-25.1327412")
        self.x_max_input.setPlaceholderText("xmax")
        self.x_max_input.setText("25.1327412")
        domain_layout.addWidget(self.x_min_input)
        domain_layout.addWidget(self.x_max_input)
        layout.addLayout(domain_layout)

        layout.addWidget(QLabel("Tempo final tf:", self))
        self.tf_input.setPlaceholderText("Ex.: 2.0")
        self.tf_input.setText("25.1327412")
        layout.addWidget(self.tf_input)

        layout.addWidget(QLabel("N da solucao exata:", self))
        self.n_input.setPlaceholderText("Ex.: 8")
        self.n_input.setText("8")
        layout.addWidget(self.n_input)

        layout.addWidget(QLabel("Vetor Nt de passos no tempo:", self))
        self.time_steps_input.setPlaceholderText("Ex.: 10, 25, 50, 100")
        self.time_steps_input.setText("10, 25, 50, 100")
        layout.addWidget(self.time_steps_input)

        layout.addWidget(QLabel("Metodos de avanco no tempo:", self))
        methods_layout = QVBoxLayout()
        for method in available_time_methods():
            checkbox = QCheckBox(f"{method.label} - {method.description}", self)
            checkbox.setChecked(True)
            checkbox.setProperty("method_id", method.identifier)
            self.method_checkboxes.append(checkbox)
            methods_layout.addWidget(checkbox)
        layout.addLayout(methods_layout)

        help_label = QLabel(
            "O grafico compara a solucao inicial t = 0, a solucao exata em tf e os metodos temporais escolhidos para diferentes valores de Nt.",
            self,
        )
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        apply_button = QPushButton("Aplicar e Plotar", self)
        layout.addWidget(apply_button)

        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #5c677d;")
        self.status_label.setText("Defina os parametros, selecione os metodos e clique em Aplicar e Plotar.")
        layout.addWidget(self.status_label)
        layout.addStretch()

        apply_button.clicked.connect(self.emit_selection)
        self.function_combo_box.currentIndexChanged.connect(self.emit_selection)
        self.x_min_input.returnPressed.connect(self.emit_selection)
        self.x_max_input.returnPressed.connect(self.emit_selection)
        self.tf_input.returnPressed.connect(self.emit_selection)
        self.n_input.returnPressed.connect(self.emit_selection)
        self.time_steps_input.returnPressed.connect(self.emit_selection)

    def selected_time_methods(self) -> list[object]:
        selected_methods: list[object] = []
        for checkbox in self.method_checkboxes:
            if checkbox.isChecked():
                method = find_time_method_by_id(str(checkbox.property("method_id")))
                if method is not None:
                    selected_methods.append(method)
        return selected_methods

    def emit_selection(self) -> None:
        try:
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
            tf = float(self.tf_input.text())
            n_value = int(self.n_input.text())
        except ValueError:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Informe xmin, xmax, tf e N com valores validos.")
            return

        if x_min >= x_max:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("O dominio deve satisfazer xmin < xmax.")
            return

        if tf < 0.0:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Informe um tempo final tf valido.")
            return

        if n_value <= 0:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Informe um N inteiro maior que zero.")
            return

        time_steps_values = parse_int_values(self.time_steps_input.text())
        time_steps_values = [value for value in time_steps_values if value > 0]
        if not time_steps_values:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Informe pelo menos um Nt inteiro maior que zero.")
            return

        selected_methods = self.selected_time_methods()
        if not selected_methods:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Selecione pelo menos um metodo de avanco no tempo.")
            return

        function = find_function_by_id(str(self.function_combo_box.currentData()))
        if function is None:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Selecione uma funcao valida.")
            return

        method_names = ", ".join(method.label for method in selected_methods)
        self.status_label.setStyleSheet("color: #2b8a3e;")
        self.status_label.setText(
            f"Aplicado: x em [{x_min:.6g}, {x_max:.6g}], tf = {tf:.6g}, N = {n_value}, Nt = {{{self.time_steps_input.text().strip()}}}, metodos = {method_names}."
        )
        self.function_selected.emit(function, x_min, x_max, tf, n_value, time_steps_values, selected_methods)
