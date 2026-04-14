from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QUrl

from . import burgers_backend


Evaluator = Callable[[float, float, int], float]


@dataclass(frozen=True)
class NamedFunction:
    identifier: str
    label: str
    description: str
    evaluator: Evaluator


def available_functions() -> list[NamedFunction]:
    return [
        NamedFunction(
            identifier="burgers_phi",
            label="Solucao de Burgers em funcao de &Phi;: <i>u</i>(<i>x</i>,<i>t</i>,<i>N</i>)",
            description="u(x, t, N) = c - 2 nu Phi_x / Phi",
            evaluator=burgers_backend.solution_u,
        )
    ]


def find_function_by_id(identifier: str) -> NamedFunction | None:
    for function in available_functions():
        if function.identifier == identifier:
            return function
    return None


def formulations_html() -> str:
    return """
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {
            font-family: "Segoe UI", sans-serif;
            color: #1f2933;
            background: #f8fafc;
            margin: 20px;
          }
          h1, h2 { color: #102a43; }
          .card {
            background: white;
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
          }
          .eq {
            font-family: "Cambria Math", "Times New Roman", serif;
            font-size: 22px;
            color: #243b53;
            text-align: center;
            overflow-x: auto;
            padding: 10px 0;
          }
          .caption { color: #486581; margin-bottom: 10px; }
          .banner {
            background: linear-gradient(135deg, #e0f2fe, #f8fafc);
            border: 1px solid #bae6fd;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 18px;
          }
        </style>
      </head>
      <body>
        <h1>Class 3: avancos em tempo e em x</h1>
        <div class="banner">
          O app discretiza a equacao viscosa de Burgers em uma malha periodica em x e avanca no tempo ate tf.
        </div>
        <div class="card">
          <h2>Solucao exata de referencia</h2>
          <div class="eq">u(x,t,N) = c - 2 nu Phi_x(x,t,N) / Phi(x,t,N)</div>
          <div class="eq">Phi(x,t,N) = soma de n = -N ate N de phi_n(x,t,n)</div>
        </div>
        <div class="card">
          <h2>Equacao resolvida</h2>
          <div class="eq">u_t + u u_x = nu u_xx</div>
          <div class="caption">Backend ativo: __BACKEND__</div>
        </div>
        <div class="card">
          <h2>Esquemas numericos</h2>
          <div class="eq">FTBS: u_x approx (u_i - u_i-1) / dx</div>
          <div class="eq">FTCS: u_x approx (u_i+1 - u_i-1) / (2 dx)</div>
          <div class="eq">Difusao: u_xx approx (u_i+1 - 2 u_i + u_i-1) / dx^2</div>
        </div>
      </body>
    </html>
    """.replace("__BACKEND__", burgers_backend.BACKEND_NAME)


def local_mathjax_path() -> Path | None:
    candidate_paths = [
        Path(__file__).resolve().parents[2] / "node_modules" / "mathjax" / "tex-svg.js",
        Path(__file__).resolve().parents[3] / "Class 2 - versao 2" / "node_modules" / "mathjax" / "tex-svg.js",
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            return candidate
    return None


def formulations_mathjax_html() -> str:
    mathjax_path = local_mathjax_path()
    mathjax_url = ""
    if mathjax_path is not None:
        mathjax_url = QUrl.fromLocalFile(str(mathjax_path)).toString()

    return f"""
    <html>
      <head>
        <meta charset="utf-8">
        <script>
          window.MathJax = {{
            tex: {{
              inlineMath: [['$', '$'], ['\\(', '\\)']],
              displayMath: [['$$', '$$'], ['\\[', '\\]']]
            }},
            svg: {{ fontCache: 'global' }}
          }};
        </script>
        <script src="{mathjax_url}"></script>
        <style>
          body {{
            font-family: "Segoe UI", sans-serif;
            color: #1f2933;
            background: #f8fafc;
            margin: 20px;
          }}
          h1, h2 {{ color: #102a43; }}
          h1 {{ margin-bottom: 8px; }}
          .card {{
            background: white;
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
          }}
          .eq {{
            font-size: 18px;
            padding: 10px 0;
            color: #243b53;
            overflow-x: auto;
          }}
          .caption {{ color: #486581; margin-bottom: 10px; }}
          .mono {{
            font-family: Consolas, monospace;
            font-size: 14px;
            color: #486581;
            margin-top: 8px;
          }}
          .banner {{
            background: linear-gradient(135deg, #dcfce7, #f8fafc);
            border: 1px solid #86efac;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 18px;
            color: #14532d;
          }}
        </style>
      </head>
      <body>
        <h1>Class 3: avancos em tempo e em x</h1>
        <div class="banner">Renderizacao matematica aprimorada com MathJax via PyQt6-WebEngine.</div>
        <div class="card">
          <h2>Solucao exata de referencia</h2>
          <div class="caption">Expressao fechada usada para comparar os esquemas numericos.</div>
          <div class="eq">$$u(x,t,N) = c - 2\\nu \\frac{{\\Phi_x(x,t,N)}}{{\\Phi(x,t,N)}}$$</div>
          <div class="eq">$$\\Phi(x,t,N) = \\sum_{{n=-N}}^{{N}} \\phi_n(x,t,n)$$</div>
          <div class="eq">$$\\phi_n(x,t,n) = \\exp\\left(-\\frac{{(x - ct - (2n + 1)\\pi)^2}}{{4\\nu(t + 1)}}\\right)$$</div>
          <div class="mono">Backend ativo: {burgers_backend.BACKEND_NAME}</div>
        </div>
        <div class="card">
          <h2>Equacao resolvida</h2>
          <div class="eq">$$u_t + u u_x = \\nu u_{{xx}}$$</div>
          <div class="caption">A aproximacao numerica usa malha periodica uniforme em x e avancos explicitos no tempo.</div>
        </div>
        <div class="card">
          <h2>Esquemas numericos</h2>
          <div class="eq">$$u_x \\approx \\frac{{u_i - u_{{i-1}}}}{{\\Delta x}} \\quad \\text{{(FTBS)}}$$</div>
          <div class="eq">$$u_x \\approx \\frac{{u_{{i+1}} - u_{{i-1}}}}{{2\\Delta x}} \\quad \\text{{(FTCS)}}$$</div>
          <div class="eq">$$u_{{xx}} \\approx \\frac{{u_{{i+1}} - 2u_i + u_{{i-1}}}}{{\\Delta x^2}}$$</div>
          <div class="eq">$$u_i^{{n+1}} = \\frac{{u_{{i-1}}^n + u_{{i+1}}^n}}{{2}} - \\Delta t\\,u_i^n\\,u_x + \\Delta t\\,\\nu\\,u_{{xx}} \\quad \\text{{(Lax-Friedrichs + difusao)}}$$</div>
        </div>
      </body>
    </html>
    """
