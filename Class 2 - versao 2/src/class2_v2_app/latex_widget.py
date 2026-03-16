from __future__ import annotations

from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    QWebEngineView = None
    HAS_WEBENGINE = False

from .function_catalog import formulations_html, formulations_mathjax_html


class LatexWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        if HAS_WEBENGINE:
            self.viewer = QWebEngineView(self)
            self.viewer.setHtml(formulations_mathjax_html())
        else:
            self.viewer = QTextBrowser(self)
            self.viewer.setOpenExternalLinks(True)
            self.viewer.setHtml(formulations_html())

        layout.addWidget(self.viewer)
