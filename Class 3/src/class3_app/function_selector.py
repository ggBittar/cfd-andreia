from __future__ import annotations

import re

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAbstractTextDocumentLayout, QPainter, QTextDocument
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QStyleOptionComboBox,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from .function_catalog import available_functions, find_function_by_id
from .space_time_method_catalog import available_space_time_methods, find_space_time_method_by_id


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


def rich_label(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setWordWrap(True)
    return label


class RichTextItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index) -> None:
        options = option
        self.initStyleOption(options, index)
        options.text = ""
        style = options.widget.style() if options.widget is not None else None

        if style is not None:
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, options, painter, options.widget)
            text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, options, options.widget)
        else:
            text_rect = options.rect

        document = QTextDocument()
        document.setHtml(index.data() or "")
        painter.save()
        painter.translate(text_rect.topLeft())
        document.setTextWidth(text_rect.width())
        context = QAbstractTextDocumentLayout.PaintContext()
        document.documentLayout().draw(painter, context)
        painter.restore()

    def sizeHint(self, option, index):
        document = QTextDocument()
        document.setHtml(index.data() or "")
        document.setTextWidth(320)
        size = document.size().toSize()
        size.setHeight(max(size.height() + 8, 24))
        return size


class RichTextComboBox(QComboBox):
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = ""

        style = self.style()
        style.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option, painter, self)
        text_rect = style.subControlRect(
            QStyle.ComplexControl.CC_ComboBox,
            option,
            QStyle.SubControl.SC_ComboBoxEditField,
            self,
        )

        document = QTextDocument()
        document.setHtml(self.currentText())
        painter.save()
        painter.translate(text_rect.topLeft())
        document.setTextWidth(text_rect.width())
        context = QAbstractTextDocumentLayout.PaintContext()
        document.documentLayout().draw(painter, context)
        painter.restore()


class FunctionSelector(QWidget):
    definition_changed = pyqtSignal(object, float, float, float, int, object, object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.function_combo_box = RichTextComboBox(self)
        self.x_min_input = QLineEdit(self)
        self.x_max_input = QLineEdit(self)
        self.tf_input = QLineEdit(self)
        self.n_input = QLineEdit(self)
        self.space_steps_input = QLineEdit(self)
        self.time_steps_input = QLineEdit(self)
        self.status_label = QLabel(self)
        self.method_checkboxes: list[QCheckBox] = []

        layout = QVBoxLayout(self)

        title = rich_label(
            "Selecione a funcao, o dominio em <i>x</i>, o tempo final <i>t</i><sub>f</sub>, "
            "a referencia exata <i>N</i> e os vetores <i>N</i><sub>x</sub> e <i>N</i><sub>t</sub> "
            "para comparar avancos em espaco e tempo. "
            "Os esquemas usam &Delta;<i>x</i>, &Delta;<i>t</i> e a viscosidade &nu;.",
            self,
        )
        layout.addWidget(title)

        layout.addWidget(rich_label("Funcao:", self))
        self.function_combo_box.setItemDelegate(RichTextItemDelegate(self.function_combo_box))
        for function in available_functions():
            self.function_combo_box.addItem(function.label, function.identifier)
        layout.addWidget(self.function_combo_box)

        layout.addWidget(rich_label("Dominio de <i>x</i>:", self))
        domain_layout = QHBoxLayout()
        self.x_min_input.setText("-25.1327412")
        self.x_max_input.setText("25.1327412")
        self.x_min_input.setPlaceholderText("x_min")
        self.x_max_input.setPlaceholderText("x_max")
        domain_layout.addWidget(self.x_min_input)
        domain_layout.addWidget(self.x_max_input)
        layout.addLayout(domain_layout)

        layout.addWidget(rich_label("Tempo final <i>t</i><sub>f</sub>:", self))
        self.tf_input.setText("1.0")
        layout.addWidget(self.tf_input)

        layout.addWidget(rich_label("<i>N</i> da solucao exata:", self))
        self.n_input.setText("8")
        layout.addWidget(self.n_input)

        layout.addWidget(rich_label("Vetor <i>N</i><sub>x</sub> de subintervalos espaciais:", self))
        self.space_steps_input.setPlaceholderText("Ex.: 40, 80, 160")
        self.space_steps_input.setText("40, 80, 160")
        layout.addWidget(self.space_steps_input)

        layout.addWidget(rich_label("Vetor <i>N</i><sub>t</sub> de passos no tempo:", self))
        self.time_steps_input.setPlaceholderText("Ex.: 50, 100, 200")
        self.time_steps_input.setText("50, 100, 200")
        layout.addWidget(self.time_steps_input)

        layout.addWidget(rich_label("Esquemas espaco-temporais:", self))
        methods_layout = QVBoxLayout()
        for method in available_space_time_methods():
            checkbox = QCheckBox(f"{method.label} - {method.description}", self)
            checkbox.setChecked(method.identifier == "ftbs")
            checkbox.setProperty("method_id", method.identifier)
            self.method_checkboxes.append(checkbox)
            methods_layout.addWidget(checkbox)
        layout.addLayout(methods_layout)

        help_label = rich_label(
            "O grafico mostra a condicao inicial, a solucao exata em <i>t</i><sub>f</sub> e as solucoes "
            "numericas para cada combinacao de <i>N</i><sub>x</sub>, <i>N</i><sub>t</sub>, "
            "&Delta;<i>x</i>, &Delta;<i>t</i> e esquema selecionado.",
            self,
        )
        layout.addWidget(help_label)

        notation_help = rich_label(
            "Notacao: &Delta;<i>x</i> = passo espacial, "
            "&Delta;<i>t</i> = passo temporal, &nu; = viscosidade, &Phi; = funcao auxiliar da solucao exata.",
            self,
        )
        notation_help.setStyleSheet("color: #5c677d; font-size: 12px;")
        layout.addWidget(notation_help)

        apply_button = QPushButton("Aplicar e Plotar", self)
        layout.addWidget(apply_button)

        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #5c677d;")
        self.status_label.setText(
            "Defina os parametros, incluindo <i>t</i><sub>f</sub>, <i>N</i><sub>x</sub> e <i>N</i><sub>t</sub>, "
            "e clique em Aplicar e Plotar. O solver calcula &Delta;<i>x</i>, &Delta;<i>t</i> e usa &nu; internamente."
        )
        layout.addWidget(self.status_label)
        layout.addStretch()

        apply_button.clicked.connect(self.emit_selection)
        self.function_combo_box.currentIndexChanged.connect(self.emit_selection)
        self.x_min_input.returnPressed.connect(self.emit_selection)
        self.x_max_input.returnPressed.connect(self.emit_selection)
        self.tf_input.returnPressed.connect(self.emit_selection)
        self.n_input.returnPressed.connect(self.emit_selection)
        self.space_steps_input.returnPressed.connect(self.emit_selection)
        self.time_steps_input.returnPressed.connect(self.emit_selection)

    def selected_methods(self) -> list[object]:
        selected_methods: list[object] = []
        for checkbox in self.method_checkboxes:
            if checkbox.isChecked():
                method = find_space_time_method_by_id(str(checkbox.property("method_id")))
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
            self.status_label.setText(
                "Informe <i>x</i><sub>min</sub>, <i>x</i><sub>max</sub>, <i>t</i><sub>f</sub> e <i>N</i> com valores validos."
            )
            return

        if x_min >= x_max:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("O dominio deve satisfazer xmin < xmax.")
            return

        if tf < 0.0:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Informe um tempo final <i>t</i><sub>f</sub> valido.")
            return

        if n_value <= 0:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Informe um <i>N</i> inteiro maior que zero.")
            return

        nx_values = [value for value in parse_int_values(self.space_steps_input.text()) if value >= 3]
        if not nx_values:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Informe pelo menos um <i>N</i><sub>x</sub> inteiro maior ou igual a 3.")
            return

        nt_values = [value for value in parse_int_values(self.time_steps_input.text()) if value > 0]
        if not nt_values:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Informe pelo menos um <i>N</i><sub>t</sub> inteiro maior que zero.")
            return

        selected_methods = self.selected_methods()
        if not selected_methods:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Selecione pelo menos um esquema espaco-temporal.")
            return

        function = find_function_by_id(str(self.function_combo_box.currentData()))
        if function is None:
            self.status_label.setStyleSheet("color: #a61e4d;")
            self.status_label.setText("Selecione uma funcao valida.")
            return

        method_names = ", ".join(method.label for method in selected_methods)
        self.status_label.setStyleSheet("color: #2b8a3e;")
        self.status_label.setText(
            f"Aplicado: <i>x</i> em [{x_min:.6g}, {x_max:.6g}], "
            f"<i>t</i><sub>f</sub> = {tf:.6g}, <i>N</i> = {n_value}, "
            f"<i>N</i><sub>x</sub> = {{{self.space_steps_input.text().strip()}}}, "
            f"<i>N</i><sub>t</sub> = {{{self.time_steps_input.text().strip()}}}, "
            f"metodos = {method_names}."
        )
        self.definition_changed.emit(function, x_min, x_max, tf, n_value, nx_values, nt_values, selected_methods)
