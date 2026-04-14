from __future__ import annotations

import math
from dataclasses import dataclass, field

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, QPainterPath, QPen, QWheelEvent
from PyQt6.QtWidgets import QWidget

from .heat_backend import evaluate_initial_curve, evaluate_steady_curve, solve_heat_1d
from .selector_widget import SolverConfiguration

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


@dataclass
class MethodResult:
    method_id: str
    label: str
    x_values: list[float]
    history_values: list[list[float]]
    time_values: list[float]
    dx: float
    dt: float
    max_error: float
    color: QColor


METHOD_COLORS = [
    QColor(84, 191, 160),
    QColor(247, 180, 68),
    QColor(114, 164, 255),
    QColor(239, 105, 80),
]


class GraphWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.curves: list[CurveData] = []
        self.method_results: list[MethodResult] = []
        self.method_notes: list[str] = []
        self.error_message = ""
        self.configuration: SolverConfiguration | None = None
        self.current_time_index = 0
        self.visible_x_min = 0.0
        self.visible_x_max = 1.0
        self.visible_y_min = 0.0
        self.visible_y_max = 1.0
        self.summary_label = ""
        self.setMinimumSize(480, 360)
        self.setAutoFillBackground(True)

    def set_configuration(self, configuration: SolverConfiguration) -> None:
        self.configuration = configuration
        self.recompute_curves()

    def recompute_curves(self) -> None:
        self.curves.clear()
        self.method_results.clear()
        self.method_notes.clear()
        self.error_message = ""
        self.summary_label = ""

        if self.configuration is None:
            self.update()
            return

        config = self.configuration
        x_values = [
            config.x_min + (config.x_max - config.x_min) * (index / (SAMPLE_COUNT - 1))
            for index in range(SAMPLE_COUNT)
        ]
        initial_curve = evaluate_initial_curve(x_values, config.initial_temperature)
        self._append_curve(
            "Condicao inicial",
            x_values,
            initial_curve,
            QColor(190, 198, 212),
            Qt.PenStyle.DotLine,
            2.0,
        )

        steady_curve = evaluate_steady_curve(x_values, config.x_min, config.x_max, config.boundary_params)
        self._append_curve(
            "Regime permanente de referencia",
            x_values,
            steady_curve,
            QColor(244, 244, 245),
            Qt.PenStyle.SolidLine,
            3.0,
        )

        for method_index, method_id in enumerate(config.space_method_ids):
            try:
                result = solve_heat_1d(
                    config.x_min,
                    config.x_max,
                    config.space_steps,
                    config.time_steps,
                    config.alpha,
                    config.boundary_params,
                    config.initial_temperature,
                    config.tf,
                    config.boundary_id,
                    method_id,
                )
            except ValueError as exc:
                self.method_notes.append(f"{self._method_label(method_id)}: {exc}")
                continue

            self.method_results.append(
                MethodResult(
                    method_id=method_id,
                    label=self._method_label(method_id),
                    x_values=result.x_values,
                    history_values=result.history_values,
                    time_values=result.time_values,
                    dx=result.dx,
                    dt=result.dt,
                    max_error=result.max_error,
                    color=METHOD_COLORS[method_index % len(METHOD_COLORS)],
                )
            )

        if not self.method_results:
            self.error_message = " | ".join(self.method_notes) if self.method_notes else "Nenhum metodo valido para plotagem."
            self.update()
            return

        self.current_time_index = min(
            config.time_steps,
            max(len(method_result.time_values) - 1 for method_result in self.method_results),
        )
        self._rebuild_method_curves()
        self.reset_zoom()
        self.update()

    def _method_label(self, method_id: str) -> str:
        label_map = {
            "null_volume": "Volume nulo",
            "semi_volume": "Semivolume",
            "ghost_element": "Elemento fantasma",
        }
        return label_map.get(method_id, method_id)

    def _rebuild_method_curves(self) -> None:
        self.curves = [curve for curve in self.curves if not curve.label.startswith("Metodo espacial |")]
        summary_parts: list[str] = []
        active_time = 0.0

        for method_result in self.method_results:
            time_index = min(self.current_time_index, len(method_result.history_values) - 1)
            current_values = method_result.history_values[time_index]
            active_time = method_result.time_values[time_index]
            self._append_curve(
                f"Metodo espacial | {method_result.label}",
                method_result.x_values,
                current_values,
                method_result.color,
                Qt.PenStyle.DashLine,
                2.8,
            )
            summary_parts.append(
                f"{method_result.label}: dx = {method_result.dx:.4g}, erro = {method_result.max_error:.4e}"
            )

        summary = (
            f"t = {active_time:.4g} | passo {self.current_time_index}/{self.configuration.time_steps} | "
            + " | ".join(summary_parts)
            + " | scroll = tempo, Ctrl+scroll = zoom"
        )
        if self.method_notes:
            summary += " | avisos: " + " ; ".join(self.method_notes)
        self.summary_label = summary

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
        if self.configuration is None:
            self.visible_x_min = 0.0
            self.visible_x_max = 1.0
            self.visible_y_min = 0.0
            self.visible_y_max = 1.0
            return

        self.visible_x_min = self.configuration.x_min
        self.visible_x_max = self.configuration.x_max

        if not self.curves:
            self.visible_y_min = 0.0
            self.visible_y_max = 1.0
            return

        y_values = [point.y() for curve in self.curves for point in curve.samples]
        y_min = min(y_values)
        y_max = max(y_values)
        if abs(y_max - y_min) < 1e-12:
            y_min -= 1.0
            y_max += 1.0
        else:
            margin = 0.15 * (y_max - y_min)
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

        if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            direction = 1 if event.angleDelta().y() > 0 else -1
            max_index = max(len(method_result.time_values) - 1 for method_result in self.method_results)
            new_index = max(0, min(max_index, self.current_time_index + direction))
            if new_index != self.current_time_index:
                self.current_time_index = new_index
                self._rebuild_method_curves()
                self.reset_zoom()
                self.update()
            event.accept()
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

        for curve in self.curves:
            path = QPainterPath()
            first_point = True
            for sample in curve.samples:
                mapped = self.map_to_screen(sample, plot_rect, x_min, x_max, y_min, y_max)
                if first_point:
                    path.moveTo(mapped)
                    first_point = False
                else:
                    path.lineTo(mapped)
            pen = QPen(curve.color, curve.width)
            pen.setStyle(curve.pen_style)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawPath(path)

            if curve.label.startswith("Metodo espacial |"):
                painter.setBrush(curve.color)
                painter.setPen(QPen(curve.color, 1.0))
                for sample in curve.samples:
                    mapped = self.map_to_screen(sample, plot_rect, x_min, x_max, y_min, y_max)
                    painter.drawEllipse(mapped, 3.0, 3.0)

        legend_height = min(plot_rect.height() - 20, 28 + len(self.curves) * 22)
        legend_box = QRectF(plot_rect.right() - 260, plot_rect.top() + 10, 250, legend_height)
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
            painter.drawText(
                QRectF(legend_box.left() + 36, legend_y - 9, legend_box.width() - 42, 18),
                int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                curve.label,
            )
            legend_y += 22

        painter.setPen(QColor(214, 220, 230))
        painter.drawText(
            QRectF(plot_rect.left(), 0, plot_rect.width(), 18),
            int(Qt.AlignmentFlag.AlignCenter),
            "Class 4 | Equacao do calor 1D por volumes finitos",
        )
        if self.summary_label:
            painter.drawText(
                QRectF(plot_rect.left(), self.height() - 20, plot_rect.width(), 16),
                int(Qt.AlignmentFlag.AlignCenter),
                self.summary_label,
            )
