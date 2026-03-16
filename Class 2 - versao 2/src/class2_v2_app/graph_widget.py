from __future__ import annotations

import math
from dataclasses import dataclass, field

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, QPainterPath, QPen, QWheelEvent
from PyQt6.QtWidgets import QWidget

from .function_catalog import NamedFunction
from .time_method_catalog import TimeMethod, advance_curve, evaluate_exact_curve

LEFT_MARGIN = 52
RIGHT_MARGIN = 20
TOP_MARGIN = 20
BOTTOM_MARGIN = 36
GRID_LINES = 8
SAMPLE_COUNT = 400


@dataclass
class CurveData:
    label: str
    samples: list[QPointF] = field(default_factory=list)
    color: QColor = field(default_factory=lambda: QColor(84, 191, 160))
    width: float = 2.0
    pen_style: Qt.PenStyle = Qt.PenStyle.SolidLine


def color_for_index(index: int) -> QColor:
    palette = [
        QColor(84, 191, 160),
        QColor(235, 125, 89),
        QColor(106, 160, 255),
        QColor(232, 193, 112),
        QColor(192, 132, 252),
        QColor(123, 203, 111),
    ]
    return palette[index % len(palette)]


def method_style(method_id: str) -> tuple[Qt.PenStyle, float]:
    styles = {
        "forward": (Qt.PenStyle.DashDotLine, 2.0),
        "backward": (Qt.PenStyle.DotLine, 2.0),
        "central": (Qt.PenStyle.DashLine, 2.4),
    }
    return styles.get(method_id, (Qt.PenStyle.SolidLine, 2.0))


class GraphWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.curves: list[CurveData] = []
        self.error_message = ""
        self.x_min = 0.0
        self.x_max = 1.0
        self.tf = 0.0
        self.n_value = 1
        self.time_steps_values: list[int] = []
        self.visible_x_min = 0.0
        self.visible_x_max = 1.0
        self.visible_y_min = -1.0
        self.visible_y_max = 1.0
        self.selected_function: NamedFunction | None = None
        self.selected_methods: list[TimeMethod] = []

        self.setMinimumSize(420, 320)
        self.setAutoFillBackground(True)

    def set_plot_definition(
        self,
        function: NamedFunction,
        x_min: float,
        x_max: float,
        tf: float,
        n_value: int,
        time_steps_values: list[int],
        selected_methods: list[TimeMethod],
    ) -> None:
        self.selected_function = function
        self.x_min = x_min
        self.x_max = x_max
        self.tf = tf
        self.n_value = n_value
        self.time_steps_values = list(time_steps_values)
        self.selected_methods = list(selected_methods)
        self.error_message = ""
        self.curves.clear()

        if self.selected_function is None:
            self.error_message = "Selecione uma funcao valida."
            self.update()
            return

        self.recompute_curves()

    def recompute_curves(self) -> None:
        self.curves.clear()
        self.error_message = ""

        if self.selected_function is None:
            self.update()
            return

        x_values = [
            self.x_min + (self.x_max - self.x_min) * (sample / (SAMPLE_COUNT - 1))
            for sample in range(SAMPLE_COUNT)
        ]

        initial_curve = evaluate_exact_curve(self.selected_function.evaluator, x_values, 0.0, self.n_value)
        self._append_curve(
            label=f"t = 0 | N = {self.n_value}",
            x_values=x_values,
            y_values=initial_curve,
            color=QColor(190, 198, 212),
            pen_style=Qt.PenStyle.DashLine,
            width=1.8,
        )

        final_exact_curve = evaluate_exact_curve(self.selected_function.evaluator, x_values, self.tf, self.n_value)
        self._append_curve(
            label=f"Exata tf | N = {self.n_value}",
            x_values=x_values,
            y_values=final_exact_curve,
            color=QColor(255, 255, 255),
            pen_style=Qt.PenStyle.SolidLine,
            width=3.0,
        )

        for nt_index, nt_value in enumerate(self.time_steps_values):
            nt_color = color_for_index(nt_index)
            for method in self.selected_methods:
                method_curve = advance_curve(
                    self.selected_function.evaluator,
                    x_values,
                    self.tf,
                    nt_value,
                    self.n_value,
                    method.identifier,
                )
                pen_style, width = method_style(method.identifier)
                self._append_curve(
                    label=f"{method.label} | Nt = {nt_value}",
                    x_values=x_values,
                    y_values=method_curve,
                    color=nt_color,
                    pen_style=pen_style,
                    width=width,
                )

        if not self.curves:
            self.error_message = "Nenhuma curva valida foi gerada para o grafico."

        self.reset_zoom()
        self.update()

    def _append_curve(
        self,
        label: str,
        x_values: list[float],
        y_values: list[float],
        color: QColor,
        pen_style: Qt.PenStyle,
        width: float,
    ) -> None:
        curve = CurveData(label=label, color=color, pen_style=pen_style, width=width)
        for x_value, y_value in zip(x_values, y_values):
            if math.isfinite(y_value):
                curve.samples.append(QPointF(x_value, y_value))
        if curve.samples:
            self.curves.append(curve)

    def plot_area(self) -> QRectF:
        return QRectF(
            LEFT_MARGIN,
            TOP_MARGIN,
            max(120, self.width() - LEFT_MARGIN - RIGHT_MARGIN),
            max(120, self.height() - TOP_MARGIN - BOTTOM_MARGIN),
        )

    def map_to_screen(self, point: QPointF, area: QRectF, x_min: float, x_max: float, y_min: float, y_max: float) -> QPointF:
        x_ratio = (point.x() - x_min) / (x_max - x_min)
        y_ratio = (point.y() - y_min) / (y_max - y_min)
        return QPointF(area.left() + x_ratio * area.width(), area.bottom() - y_ratio * area.height())

    def map_to_model_x(self, x_screen: float, area: QRectF, x_min: float, x_max: float) -> float:
        ratio = (x_screen - area.left()) / area.width()
        return x_min + ratio * (x_max - x_min)

    def reset_zoom(self) -> None:
        self.visible_x_min = self.x_min
        self.visible_x_max = self.x_max

        if not self.curves:
            self.visible_y_min = -1.0
            self.visible_y_max = 1.0
            return

        y_values = [point.y() for curve in self.curves for point in curve.samples]
        y_min = min(y_values)
        y_max = max(y_values)

        if abs(y_max - y_min) < 1e-9:
            y_min -= 1.0
            y_max += 1.0
        else:
            margin = (y_max - y_min) * 0.15
            y_min -= margin
            y_max += margin

        self.visible_y_min = y_min
        self.visible_y_max = y_max

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if not self.curves or self.error_message:
            event.ignore()
            return
        area = self.plot_area()
        if not area.contains(event.position()):
            event.ignore()
            return
        x_min = self.visible_x_min
        x_max = self.visible_x_max
        y_min = self.visible_y_min
        y_max = self.visible_y_max
        factor = 0.85 if event.angleDelta().y() > 0 else 1.15
        center_x = self.map_to_model_x(event.position().x(), area, x_min, x_max)
        center_y = y_max - ((event.position().y() - area.top()) / area.height()) * (y_max - y_min)
        new_width = max(0.001, (x_max - x_min) * factor)
        new_height = max(0.001, (y_max - y_min) * factor)
        ratio_x = (center_x - x_min) / (x_max - x_min)
        ratio_y = (center_y - y_min) / (y_max - y_min)
        self.visible_x_min = center_x - ratio_x * new_width
        self.visible_x_max = self.visible_x_min + new_width
        self.visible_y_min = center_y - ratio_y * new_height
        self.visible_y_max = self.visible_y_min + new_height
        self.update()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_zoom()
            self.update()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(20, 24, 31))
        plot_rect = self.plot_area()
        painter.setPen(QColor(58, 66, 84))
        painter.drawRoundedRect(plot_rect.adjusted(-1.0, -1.0, 1.0, 1.0), 10.0, 10.0)
        if self.error_message:
            painter.setPen(QColor(226, 149, 120))
            painter.drawText(plot_rect, int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.TextWordWrap), self.error_message)
            return
        if not self.curves:
            painter.setPen(QColor(160, 171, 190))
            painter.drawText(plot_rect, int(Qt.AlignmentFlag.AlignCenter), "Aguardando parametros para plotagem.")
            return
        x_min = self.visible_x_min
        x_max = self.visible_x_max
        y_min = self.visible_y_min
        y_max = self.visible_y_max
        grid_pen = QPen(QColor(44, 50, 63))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for index in range(GRID_LINES + 1):
            ratio = index / GRID_LINES
            x = plot_rect.left() + ratio * plot_rect.width()
            y = plot_rect.top() + ratio * plot_rect.height()
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))
            x_value = x_min + ratio * (x_max - x_min)
            y_value = y_max - ratio * (y_max - y_min)
            painter.setPen(QColor(130, 141, 160))
            painter.drawText(QRectF(x - 28, plot_rect.bottom() + 6, 56, 16), int(Qt.AlignmentFlag.AlignCenter), f"{x_value:.4g}")
            painter.drawText(QRectF(4, y - 8, LEFT_MARGIN - 10, 16), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), f"{y_value:.4g}")
            painter.setPen(grid_pen)
        axis_pen = QPen(QColor(115, 132, 158))
        axis_pen.setWidth(2)
        painter.setPen(axis_pen)
        if x_min <= 0.0 <= x_max:
            painter.drawLine(self.map_to_screen(QPointF(0.0, y_max), plot_rect, x_min, x_max, y_min, y_max), self.map_to_screen(QPointF(0.0, y_min), plot_rect, x_min, x_max, y_min, y_max))
        if y_min <= 0.0 <= y_max:
            painter.drawLine(self.map_to_screen(QPointF(x_min, 0.0), plot_rect, x_min, x_max, y_min, y_max), self.map_to_screen(QPointF(x_max, 0.0), plot_rect, x_min, x_max, y_min, y_max))
        for curve in self.curves:
            path = QPainterPath()
            first_point = True
            for sample in curve.samples:
                if sample.x() < x_min or sample.x() > x_max:
                    first_point = True
                    continue
                mapped = self.map_to_screen(sample, plot_rect, x_min, x_max, y_min, y_max)
                if first_point:
                    path.moveTo(mapped)
                    first_point = False
                else:
                    path.lineTo(mapped)
            pen = QPen(curve.color, curve.width)
            pen.setStyle(curve.pen_style)
            painter.setPen(pen)
            painter.drawPath(path)
        legend_height = 28 + len(self.curves) * 22
        legend_box = QRectF(plot_rect.right() - 290, plot_rect.top() + 10, 280, legend_height)
        painter.setPen(QColor(58, 66, 84))
        painter.setBrush(QColor(16, 20, 26, 215))
        painter.drawRoundedRect(legend_box, 8.0, 8.0)
        legend_y = int(legend_box.top()) + 14
        for curve in self.curves:
            pen = QPen(curve.color, 2)
            pen.setStyle(curve.pen_style)
            painter.setPen(pen)
            painter.drawLine(QPointF(legend_box.left() + 10, legend_y), QPointF(legend_box.left() + 30, legend_y))
            painter.setPen(QColor(230, 235, 242))
            painter.drawText(QRectF(legend_box.left() + 36, legend_y - 9, legend_box.width() - 42, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), curve.label)
            legend_y += 22
        painter.setPen(QColor(214, 220, 230))
        painter.drawText(QRectF(plot_rect.left(), 0, plot_rect.width(), 18), int(Qt.AlignmentFlag.AlignCenter), f"Comparacao temporal | t = 0, tf = {self.tf:.3f}, N = {self.n_value}")
