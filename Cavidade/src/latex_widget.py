from __future__ import annotations

import html
import re
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QFrame,
)

from latex_content import LATEX_TEXT


class LatexGuideWidget(QWidget):
    """
    Guia visual da discretização.

    A versão anterior usava QTextBrowser com uma conversão LaTeX -> HTML muito simples.
    Em temas escuros do Qt/Windows isso fazia as caixas das equações ficarem brancas com
    texto quase branco. Esta versão monta a página com QLabel/QScrollArea e define cores
    explicitamente, mantendo as equações em blocos monoespaçados legíveis.
    """

    def __init__(self):
        super().__init__()
        self._tex_path = self._find_tex_file()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        toolbar = QHBoxLayout()
        title = QLabel("Discretização node-centered da cavidade com tampa deslizante")
        title.setObjectName("pageTitle")
        toolbar.addWidget(title, stretch=1)

        btn_save = QPushButton("Salvar/Exportar .tex")
        btn_save.clicked.connect(self._export_tex)
        toolbar.addWidget(btn_save)
        root.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(6, 6, 18, 18)
        self.content_layout.setSpacing(10)
        self._populate_from_latex(LATEX_TEXT)
        self.content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll)

        self.setStyleSheet(
            """
            QWidget {
                background: #202124;
                color: #f1f3f4;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 14px;
            }
            QLabel#pageTitle {
                font-size: 20px;
                font-weight: 700;
                color: #ffffff;
                padding: 4px 0 8px 0;
            }
            QLabel.section {
                font-size: 22px;
                font-weight: 700;
                color: #ffffff;
                margin-top: 8px;
                margin-bottom: 4px;
            }
            QLabel.subsection {
                font-size: 18px;
                font-weight: 700;
                color: #c7d2fe;
                margin-top: 12px;
                margin-bottom: 2px;
            }
            QLabel.paragraph {
                color: #f1f3f4;
                line-height: 145%;
            }
            QLabel.equation {
                background: #111827;
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px 12px;
                selection-background-color: #2563eb;
            }
            QPushButton {
                background: #374151;
                color: #ffffff;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 7px 12px;
            }
            QPushButton:hover { background: #4b5563; }
            QPushButton:pressed { background: #1f2937; }
            QScrollArea { border: none; }
            QScrollBar:vertical {
                background: #202124;
                width: 12px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #5f6368;
                min-height: 30px;
                border-radius: 6px;
            }
            """
        )

    def _find_tex_file(self) -> Path | None:
        here = Path(__file__).resolve()
        candidate = here.parents[1] / "docs" / "discretizacao.tex"
        return candidate if candidate.exists() else None

    def _populate_from_latex(self, text: str) -> None:
        """Converte apenas a estrutura do texto para uma guia visual legível."""
        tokens = re.split(r"(\\\[.*?\\\])", text.strip(), flags=re.DOTALL)
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            if token.startswith(r"\[") and token.endswith(r"\]"):
                eq = token[2:-2].strip()
                self._add_equation(eq)
            else:
                self._add_text_block(token)

    def _add_text_block(self, block: str) -> None:
        # Trata seções e parágrafos comuns.
        lines = [ln.strip() for ln in block.splitlines()]
        paragraph_parts: list[str] = []

        def flush_paragraph() -> None:
            if paragraph_parts:
                paragraph = " ".join(paragraph_parts).strip()
                paragraph_parts.clear()
                if paragraph:
                    self._add_paragraph(paragraph)

        for line in lines:
            if not line:
                flush_paragraph()
                continue
            sec = re.match(r"\\section\*\{(.+?)\}", line)
            sub = re.match(r"\\subsection\*\{(.+?)\}", line)
            if sec:
                flush_paragraph()
                self._add_heading(sec.group(1), section=True)
            elif sub:
                flush_paragraph()
                self._add_heading(sub.group(1), section=False)
            else:
                paragraph_parts.append(line)
        flush_paragraph()

    def _add_heading(self, text: str, section: bool) -> None:
        label = QLabel(html.escape(text))
        label.setObjectName("section" if section else "subsection")
        label.setProperty("class", "section" if section else "subsection")
        label.setWordWrap(True)
        self.content_layout.addWidget(label)

    def _add_paragraph(self, text: str) -> None:
        label = QLabel(self._inline_latex_to_html(text))
        label.setObjectName("paragraph")
        label.setProperty("class", "paragraph")
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        label.setOpenExternalLinks(False)
        self.content_layout.addWidget(label)

    def _add_equation(self, equation: str) -> None:
        label = QLabel(self._format_equation(equation))
        label.setObjectName("equation")
        label.setProperty("class", "equation")
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setWordWrap(True)
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(11)
        label.setFont(font)
        self.content_layout.addWidget(label)

    def _inline_latex_to_html(self, text: str) -> str:
        # Escapa HTML e destaca expressões inline entre $...$ sem depender de MathJax.
        escaped = html.escape(text)

        def repl(match: re.Match[str]) -> str:
            content = match.group(1)
            content = self._latex_symbols(content)
            return (
                "<span style='font-family: Consolas, monospace; color:#fde68a; "
                "background:#111827; padding:1px 4px; border-radius:4px;'>"
                + html.escape(content)
                + "</span>"
            )

        return re.sub(r"\$(.+?)\$", repl, escaped)

    def _format_equation(self, equation: str) -> str:
        eq = equation.strip()
        eq = re.sub(r"\\begin\{cases\}", "{", eq)
        eq = re.sub(r"\\end\{cases\}", "}", eq)
        eq = eq.replace(r"\\", "\n")
        eq = eq.replace(r"\qquad", "    ").replace(r"\quad", "  ")
        eq = eq.replace(r"\left", "").replace(r"\right", "")
        eq = re.sub(r"\\text\{([^}]*)\}", r"\1", eq)
        eq = self._latex_symbols(eq)
        eq = self._compact_frac(eq)
        eq = re.sub(r"\s+", " ", eq)
        eq = eq.replace(" ,", ",").replace(" .", ".")
        eq = eq.replace("\n ", "\n")
        return eq

    def _latex_symbols(self, value: str) -> str:
        replacements = {
            r"\Delta": "Δ",
            r"\partial": "∂",
            r"\nabla": "∇",
            r"\omega": "ω",
            r"\psi": "ψ",
            r"\nu": "ν",
            r"\rho": "ρ",
            r"\times": "×",
            r"\leq": "≤",
            r"\geq": "≥",
            r"\lesssim": "≲",
            r"\min": "min",
            r"\frac": "frac",
        }
        for old, new in replacements.items():
            value = value.replace(old, new)
        return value

    def _compact_frac(self, value: str) -> str:
        # Transforma frac{a}{b} em (a)/(b) para leitura direta no guia.
        pattern = re.compile(r"frac\{([^{}]+)\}\{([^{}]+)\}")
        previous = None
        while previous != value:
            previous = value
            value = pattern.sub(r"(\1)/(\2)", value)
        return value

    def _export_tex(self) -> None:
        target, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar arquivo LaTeX",
            "discretizacao.tex",
            "Arquivos LaTeX (*.tex);;Todos os arquivos (*)",
        )
        if not target:
            return
        try:
            Path(target).write_text(LATEX_TEXT, encoding="utf-8")
            QMessageBox.information(self, "Exportado", f"Arquivo salvo em:\n{target}")
        except OSError as exc:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo:\n{exc}")
