from __future__ import annotations

import math
from dataclasses import dataclass, field

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .boundary_condition_catalog import (
    BoundaryConditionMethod,
    available_boundary_conditions,
    find_boundary_condition_by_id,
)
from .space_method_catalog import available_space_methods, find_space_method_by_id


@dataclass(frozen=True)
class SolverConfiguration:
    x_min: float
    x_max: float
    space_steps: int
    time_steps: int
    requested_dx: float | None
    requested_dt: float | None
    alpha: float
    initial_temperature: float
    tf: float
    boundary_id: str
    boundary_params: dict[str, float] = field(default_factory=dict)
    space_method_ids: list[str] = field(default_factory=list)


class SelectorWidget(QWidget):
    configuration_changed = pyqtSignal(object)
    apply_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.x_min_input = QLineEdit(self)
        self.x_max_input = QLineEdit(self)
        self.space_mode_combo = QComboBox(self)
        self.space_value_input = QLineEdit(self)
        self.time_mode_combo = QComboBox(self)
        self.time_value_input = QLineEdit(self)
        self.alpha_input = QLineEdit(self)
        self.initial_temperature_input = QLineEdit(self)
        self.tf_input = QLineEdit(self)
        self.boundary_combo = QComboBox(self)
        self.space_method_list = QListWidget(self)
        self.status_label = QLabel(self)
        self.boundary_param_inputs: dict[str, QLineEdit] = {}

        self._boundary_items = available_boundary_conditions()
        self._space_items = available_space_methods()

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Configure o dominio 1D e escolha separadamente, para x e para t, "
            "se voce quer informar numero de passos ou tamanho do passo.",
            self,
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.form = QFormLayout()
        self.boundary_params_form = QFormLayout()

        self.x_min_input.setText("0.0")
        self.x_max_input.setText("1.0")
        self.space_mode_combo.addItem("Numero de passos", "steps")
        self.space_mode_combo.addItem("Tamanho do passo", "size")
        self.space_value_input.setText("20")
        self.time_mode_combo.addItem("Numero de passos", "steps")
        self.time_mode_combo.addItem("Tamanho do passo", "size")
        self.time_value_input.setText("200")
        self.alpha_input.setText("0.01")
        self.initial_temperature_input.setText("20.0")
        self.tf_input.setText("1.0")

        self.form.addRow("x_min", self.x_min_input)
        self.form.addRow("x_max", self.x_max_input)
        self.form.addRow("Modo em x", self.space_mode_combo)
        self.form.addRow("Valor em x", self.space_value_input)
        self.form.addRow("Modo no tempo", self.time_mode_combo)
        self.form.addRow("Valor no tempo", self.time_value_input)
        self.form.addRow("Alpha", self.alpha_input)
        self.form.addRow("Temperatura inicial", self.initial_temperature_input)
        self.form.addRow("Tempo final", self.tf_input)

        self._populate_combo(self.boundary_combo, self._boundary_items)
        self._populate_space_methods()
        self.form.addRow("Contorno", self.boundary_combo)
        self.form.addRow("Metodos espaciais", self.space_method_list)
        self.form.addRow(QLabel("Parametros do contorno", self))
        self.form.addRow(self._wrap_form(self.boundary_params_form))

        layout.addLayout(self.form)

        hint = QLabel(
            "Os parametros do contorno agora pertencem ao modelo selecionado. "
            "Se voce informar dx ou dt, a interface converte para Nx e Nt compativeis. "
            "Use Ctrl+clique para comparar mais de um metodo espacial.",
            self,
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #5c677d; font-size: 12px;")
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        self.apply_button = QPushButton("Aplicar e Plotar", self)
        buttons.addWidget(self.apply_button)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #5c677d;")
        self.status_label.setText("Pronto para resolver o caso transiente 1D do calor sem geracao.")
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.apply_button.clicked.connect(self.apply_configuration)
        for field in (
            self.x_min_input,
            self.x_max_input,
            self.space_value_input,
            self.time_value_input,
            self.alpha_input,
            self.initial_temperature_input,
            self.tf_input,
        ):
            field.returnPressed.connect(self.emit_configuration)
        self.space_mode_combo.currentIndexChanged.connect(self._update_mode_hints)
        self.time_mode_combo.currentIndexChanged.connect(self._update_mode_hints)
        self.boundary_combo.currentIndexChanged.connect(self._on_boundary_changed)
        self.space_method_list.itemSelectionChanged.connect(self.emit_configuration)
        self._rebuild_boundary_form()
        self._update_mode_hints()

    def _wrap_form(self, form: QFormLayout) -> QWidget:
        widget = QWidget(self)
        widget.setLayout(form)
        return widget

    def _populate_combo(self, combo: QComboBox, methods: list[object]) -> None:
        combo.clear()
        for index, method in enumerate(methods):
            suffix = "" if method.implemented else " (em breve)"
            combo.addItem(f"{method.label}{suffix}", method.identifier)
            item = combo.model().item(index)
            if item is not None and not method.implemented:
                item.setEnabled(False)
                item.setData("Disponivel em versao futura.", Qt.ItemDataRole.ToolTipRole)

    def _populate_space_methods(self) -> None:
        self.space_method_list.clear()
        self.space_method_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.space_method_list.setMinimumHeight(96)
        for method in self._space_items:
            item = QListWidgetItem(method.label)
            item.setData(Qt.ItemDataRole.UserRole, method.identifier)
            item.setToolTip(method.description)
            if not method.implemented:
                item.setText(f"{method.label} (em breve)")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.space_method_list.addItem(item)
            if method.implemented:
                item.setSelected(True)

    def _selected_space_method_ids(self) -> list[str]:
        identifiers: list[str] = []
        for item in self.space_method_list.selectedItems():
            identifier = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(identifier, str):
                identifiers.append(identifier)
        return identifiers

    def _clear_form(self, form: QFormLayout) -> None:
        while form.rowCount() > 0:
            form.removeRow(0)

    def _selected_boundary(self) -> BoundaryConditionMethod | None:
        return find_boundary_condition_by_id(str(self.boundary_combo.currentData()))

    def _rebuild_boundary_form(self) -> None:
        self._clear_form(self.boundary_params_form)
        self.boundary_param_inputs.clear()
        boundary = self._selected_boundary()
        if boundary is None:
            return

        for parameter in boundary.parameters:
            line_edit = QLineEdit(self)
            line_edit.setText(parameter.default_value)
            line_edit.setPlaceholderText(parameter.description)
            line_edit.returnPressed.connect(self.emit_configuration)
            self.boundary_param_inputs[parameter.key] = line_edit
            self.boundary_params_form.addRow(parameter.label, line_edit)

    def _on_boundary_changed(self) -> None:
        self._rebuild_boundary_form()
        self.emit_configuration()

    def _update_mode_hints(self) -> None:
        if self.space_mode_combo.currentData() == "steps":
            self.space_value_input.setPlaceholderText("Ex.: 40")
        else:
            self.space_value_input.setPlaceholderText("Ex.: 0.05")

        if self.time_mode_combo.currentData() == "steps":
            self.time_value_input.setPlaceholderText("Ex.: 200")
        else:
            self.time_value_input.setPlaceholderText("Ex.: 0.005")
        self.emit_configuration()

    def _resolve_space_steps(self, x_min: float, x_max: float) -> tuple[int, float | None]:
        mode = str(self.space_mode_combo.currentData())
        raw_value = float(self.space_value_input.text())
        if mode == "steps":
            steps = int(raw_value)
            if steps < 2:
                raise ValueError("Use pelo menos 2 passos espaciais.")
            return steps, None

        if raw_value <= 0.0:
            raise ValueError("O tamanho do passo espacial deve ser positivo.")
        domain_length = x_max - x_min
        steps = max(2, math.ceil(domain_length / raw_value))
        return steps, raw_value

    def _resolve_time_steps(self, tf: float) -> tuple[int, float | None]:
        mode = str(self.time_mode_combo.currentData())
        raw_value = float(self.time_value_input.text())
        if mode == "steps":
            steps = int(raw_value)
            if steps <= 0:
                raise ValueError("Use pelo menos 1 passo no tempo.")
            return steps, None

        if raw_value <= 0.0:
            raise ValueError("O tamanho do passo temporal deve ser positivo.")
        if tf == 0.0:
            return 1, raw_value
        steps = max(1, math.ceil(tf / raw_value))
        return steps, raw_value

    def _read_boundary_params(self, boundary: BoundaryConditionMethod) -> dict[str, float]:
        values: dict[str, float] = {}
        for parameter in boundary.parameters:
            widget = self.boundary_param_inputs.get(parameter.key)
            if widget is None:
                raise ValueError("Campo de parametro de contorno nao encontrado.")
            values[parameter.key] = float(widget.text())
        return values

    def emit_configuration(self) -> None:
        try:
            boundary = self._selected_boundary()
            if boundary is None:
                raise ValueError("Selecione uma condicao de contorno valida.")

            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
            tf = float(self.tf_input.text())
            space_steps, requested_dx = self._resolve_space_steps(x_min, x_max)
            time_steps, requested_dt = self._resolve_time_steps(tf)
            boundary_params = self._read_boundary_params(boundary)
            config = SolverConfiguration(
                x_min=x_min,
                x_max=x_max,
                space_steps=space_steps,
                time_steps=time_steps,
                requested_dx=requested_dx,
                requested_dt=requested_dt,
                alpha=float(self.alpha_input.text()),
                initial_temperature=float(self.initial_temperature_input.text()),
                tf=tf,
                boundary_id=boundary.identifier,
                boundary_params=boundary_params,
                space_method_ids=self._selected_space_method_ids(),
            )
        except ValueError:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Preencha dominio, passos, alpha, contorno e tempo final com valores validos.")
            return

        if config.x_min >= config.x_max:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("O dominio deve satisfazer x_min < x_max.")
            return

        if config.alpha <= 0.0:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("O parametro alpha deve ser positivo.")
            return

        if config.tf < 0.0:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("O tempo final deve ser nao negativo.")
            return

        boundary = find_boundary_condition_by_id(config.boundary_id)
        if boundary is None or not boundary.implemented:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("A condicao de contorno selecionada ainda nao foi implementada.")
            return

        if not config.space_method_ids:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Selecione pelo menos um metodo espacial para comparar.")
            return
        for space_method_id in config.space_method_ids:
            space_method = find_space_method_by_id(space_method_id)
            if space_method is None or not space_method.implemented:
                self.status_label.setStyleSheet("color: #a61e4d;")
                self.status_label.setText("Um dos metodos espaciais selecionados ainda nao foi implementado.")
                return

        dx = (config.x_max - config.x_min) / config.space_steps
        dt = config.tf / config.time_steps if config.tf > 0.0 else 0.0
        parts = [
            f"Aplicado: dominio = [{config.x_min:.6g}, {config.x_max:.6g}]",
            f"Nx = {config.space_steps}",
            f"Nt = {config.time_steps}",
            f"dx efetivo = {dx:.6g}",
            f"dt efetivo = {dt:.6g}",
            f"alpha = {config.alpha:.6g}",
            f"T0 = {config.initial_temperature:.6g}",
            f"contorno = {boundary.label}",
            f"metodos = {', '.join(config.space_method_ids)}",
            f"tf = {config.tf:.6g}",
        ]
        for parameter in boundary.parameters:
            value = config.boundary_params.get(parameter.key)
            if value is not None:
                parts.append(f"{parameter.label} = {value:.6g}")
        if config.requested_dx is not None:
            parts.append(f"dx pedido = {config.requested_dx:.6g}")
        if config.requested_dt is not None:
            parts.append(f"dt pedido = {config.requested_dt:.6g}")

        self.status_label.setStyleSheet("color: #2b8a3e;")
        self.status_label.setText(", ".join(parts) + ".")
        self.configuration_changed.emit(config)

    def apply_configuration(self) -> None:
        self.emit_configuration()
        if self.status_label.styleSheet() == "color: #2b8a3e;":
            self.apply_requested.emit()
