from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

try:
    from . import _burgers as burgers_backend
    BACKEND_NAME = "Cython"
except ImportError:
    from . import burgers_fallback as burgers_backend
    BACKEND_NAME = "Python fallback"


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
            identifier="exp_sum",
            label="Solucao em funcao de Phi",
            description="u(x, t, N) = c - 2 nu Phi_x(x, t, N) / Phi(x, t, N)",
            evaluator=burgers_backend.solution_u,
        )
    ]


def find_function_by_id(identifier: str) -> NamedFunction | None:
    for function in available_functions():
        if function.identifier == identifier:
            return function
    return None


def formulations_html() -> str:
    return f"""
    <html>
      <head>
        <meta charset="utf-8">
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
            font-family: "Cambria Math", "Times New Roman", serif;
            font-size: 24px;
            padding: 10px 0;
            color: #243b53;
            text-align: center;
            overflow-x: auto;
          }}
          .mono {{
            font-family: Consolas, monospace;
            font-size: 14px;
            color: #486581;
            margin-top: 8px;
            text-align: center;
          }}
          .caption {{ color: #486581; margin-bottom: 10px; }}
          .banner {{
            background: linear-gradient(135deg, #e0f2fe, #f8fafc);
            border: 1px solid #bae6fd;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 18px;
            color: #0f172a;
          }}
          .fraction {{
            display: inline-block;
            vertical-align: middle;
            text-align: center;
            line-height: 1.15;
            margin: 0 6px;
          }}
          .fraction .top {{
            display: block;
            padding: 0 10px 3px 10px;
            border-bottom: 1px solid #243b53;
          }}
          .fraction .bottom {{
            display: block;
            padding: 3px 10px 0 10px;
          }}
          .sum {{
            display: inline-block;
            position: relative;
            width: 44px;
            margin: 0 10px;
            vertical-align: middle;
          }}
          .sum .symbol {{
            display: block;
            font-size: 36px;
            line-height: 30px;
          }}
          .sum .upper {{
            position: absolute;
            top: -14px;
            left: 0;
            right: 0;
            font-size: 12px;
          }}
          .sum .lower {{
            position: absolute;
            bottom: -16px;
            left: 0;
            right: 0;
            font-size: 12px;
          }}
        </style>
      </head>
      <body>
        <h1>Formulacoes em funcao de Phi</h1>
        <div class="banner">
          Esta visualizacao usa HTML nativo do Qt. Para renderizacao matematica mais fiel, instale
          <strong>PyQt6-WebEngine</strong> e a aba usara MathJax automaticamente.
        </div>
        <div class="card">
          <h2>Funcao principal</h2>
          <div class="caption">Campo principal escrito a partir de Phi.</div>
          <div class="eq">
            u(x,t,N) = c - 2&nu;
            <span class="fraction">
              <span class="top">&Phi;<sub>x</sub>(x,t,N)</span>
              <span class="bottom">&Phi;(x,t,N)</span>
            </span>
          </div>
          <div class="mono">Backend ativo: {BACKEND_NAME}</div>
        </div>
        <div class="card">
          <h2>Funcao auxiliar Phi</h2>
          <div class="eq">
            &Phi;(x,t,N) =
            <span class="sum">
              <span class="upper">N</span>
              <span class="symbol">&sum;</span>
              <span class="lower">n = -N</span>
            </span>
            &phi;<sub>n</sub>(x,t,n)
          </div>
        </div>
        <div class="card">
          <h2>Derivada espacial</h2>
          <div class="eq">
            &Phi;<sub>x</sub>(x,t,N) =
            <span class="sum">
              <span class="upper">N</span>
              <span class="symbol">&sum;</span>
              <span class="lower">n = -N</span>
            </span>
            &phi;<sub>x,n</sub>(x,t,n)
          </div>
        </div>
        <div class="card">
          <h2>Termo elemental</h2>
          <div class="eq">
            &phi;<sub>n</sub>(x,t,n) = exp(
            -<span class="fraction">
              <span class="top">(x - ct - (2n + 1)&pi;)<sup>2</sup></span>
              <span class="bottom">4&nu;(t + 1)</span>
            </span>)
          </div>
        </div>
        <div class="card">
          <h2>Derivada do termo elemental</h2>
          <div class="eq">
            &phi;<sub>x,n</sub>(x,t,n) =
            -<span class="fraction">
              <span class="top">x - ct - (2n + 1)&pi;</span>
              <span class="bottom">2&nu;(t + 1)</span>
            </span>
            exp(...)
          </div>
        </div>
        <div class="card">
          <h2>Parametros do backend</h2>
          <div class="eq">c = 4.0, nu = 1.0</div>
        </div>
      </body>
    </html>
    """


def formulations_mathjax_html() -> str:
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
        <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
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
        <h1>Formulacoes em funcao de Phi</h1>
        <div class="banner">Renderizacao matematica aprimorada com MathJax via PyQt6-WebEngine.</div>
        <div class="card">
          <h2>Funcao principal</h2>
          <div class="caption">Campo principal escrito a partir de Phi.</div>
          <div class="eq">$$u(x,t,N) = c - 2\\nu \\frac{{\\Phi_x(x,t,N)}}{{\\Phi(x,t,N)}}$$</div>
          <div class="mono">Backend ativo: {BACKEND_NAME}</div>
        </div>
        <div class="card">
          <h2>Funcao auxiliar Phi</h2>
          <div class="eq">$$\\Phi(x,t,N) = \\sum_{{n=-N}}^{{N}} \\phi_n(x,t,n)$$</div>
        </div>
        <div class="card">
          <h2>Derivada espacial</h2>
          <div class="eq">$$\\Phi_x(x,t,N) = \\sum_{{n=-N}}^{{N}} \\phi_{{x,n}}(x,t,n)$$</div>
        </div>
        <div class="card">
          <h2>Termo elemental</h2>
          <div class="eq">$$\\phi_n(x,t,n) = \\exp\\left(-\\frac{{(x - ct - (2n + 1)\\pi)^2}}{{4\\nu(t + 1)}}\\right)$$</div>
        </div>
        <div class="card">
          <h2>Derivada do termo elemental</h2>
          <div class="eq">$$\\phi_{{x,n}}(x,t,n) = -\\frac{{x - ct - (2n + 1)\\pi}}{{2\\nu(t + 1)}} \\exp\\left(-\\frac{{(x - ct - (2n + 1)\\pi)^2}}{{4\\nu(t + 1)}}\\right)$$</div>
        </div>
        <div class="card">
          <h2>Parametros do backend</h2>
          <div class="eq">$$c = 4.0, \\quad \\nu = 1.0$$</div>
        </div>
      </body>
    </html>
    """
