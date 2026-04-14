from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    HAS_WEBENGINE = True
except ImportError:
    QWebEngineView = None
    HAS_WEBENGINE = False

from .function_catalog import formulations_html, formulations_mathjax_html, local_mathjax_path


class LatexWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        project_root = Path(__file__).resolve().parents[2]
        base_url = QUrl.fromLocalFile(str(project_root) + "/")

        if HAS_WEBENGINE and local_mathjax_path() is not None:
            self.viewer = QWebEngineView(self)
            self.viewer.setHtml(formulations_mathjax_html(), base_url)
        else:
            self.viewer = QTextBrowser(self)
            self.viewer.setHtml(formulations_html())
        layout.addWidget(self.viewer)
