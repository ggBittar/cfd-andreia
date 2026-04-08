from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl

from . import heat_backend


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
        <h1>Class 4: volumes finitos 1D</h1>
        <div class="banner">
          O app resolve a equacao transiente do calor sem geracao com malha uniforme e
          fronteiras de Dirichlet.
        </div>
        <div class="card">
          <h2>Equacao resolvida</h2>
          <div class="eq">dT/dt = alpha d²T/dx²</div>
          <div class="eq">T(x_min) = T_L, T(x_max) = T_R</div>
          <div class="eq">T(x,0) = T_0</div>
          <div class="caption">Backend ativo: __BACKEND__</div>
        </div>
        <div class="card">
          <h2>Discretizacao disponivel</h2>
          <div class="eq">T_P^(n+1) = T_P^n + Fo (T_E^n - 2T_P^n + T_W^n)</div>
          <div class="eq">Fo = alpha dt / dx²</div>
          <div class="caption">
            A interface permite definir separadamente Nx ou dx, e Nt ou dt.
            Os parametros numericos do contorno dependem do modelo de contorno selecionado.
            Os metodos espaciais disponiveis incluem volume nulo, semivolume e elemento fantasma.
          </div>
        </div>
      </body>
    </html>
    """.replace("__BACKEND__", heat_backend.BACKEND_NAME)


def local_mathjax_path() -> Path | None:
    candidate_paths = [
        Path(__file__).resolve().parents[2] / "node_modules" / "mathjax" / "tex-svg.js",
        Path(__file__).resolve().parents[3] / "Class 3" / "node_modules" / "mathjax" / "tex-svg.js",
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
              inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
              displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
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
        <h1>Class 4: volumes finitos 1D</h1>
        <div class="banner">
          Estrutura pronta para crescer em novos metodos espaciais e novas condicoes de contorno.
        </div>
        <div class="card">
          <h2>Equacao do calor transiente sem geracao</h2>
          <div class="eq">$$\\frac{{\\partial T}}{{\\partial t}} = \\alpha \\frac{{\\partial^2 T}}{{\\partial x^2}}$$</div>
          <div class="eq">$$T(x_{{min}}) = T_L, \\qquad T(x_{{max}}) = T_R$$</div>
          <div class="eq">$$T(x,0) = T_0$$</div>
          <div class="mono">Backend ativo: {heat_backend.BACKEND_NAME}</div>
        </div>
        <div class="card">
          <h2>Perfil de referencia em regime permanente</h2>
          <div class="eq">$$T(x) = T_L + (T_R - T_L)\\frac{{x - x_{{min}}}}{{x_{{max}} - x_{{min}}}}$$</div>
          <div class="caption">O grafico compara a evolucao numerica com esse perfil limite quando o tempo avanca.</div>
        </div>
        <div class="card">
          <h2>Metodos explicitos de malha espacial</h2>
          <div class="eq">$$Fo = \\frac{{\\alpha \\Delta t}}{{\\Delta x^2}}$$</div>
          <div class="eq">$$T_P^{{n+1}} = T_P^n + Fo\\left(T_E^n - 2T_P^n + T_W^n\\right)$$</div>
          <div class="eq">$$\\text{{Volume nulo: fronteiras em }}x_{{min}}, x_{{max}}\\text{{ com }}T\\text{{ imposto diretamente}}$$</div>
          <div class="eq">$$\\text{{Semivolume: centros em }}x_{{min}} + \\frac{{\\Delta x}}{{2}}, \\ldots, x_{{max}} - \\frac{{\\Delta x}}{{2}}$$</div>
          <div class="eq">$$\\text{{Elemento fantasma: volumes completos e celulas ficticias fora do dominio}}$$</div>
          <div class="eq">$$T_1^{{n+1}} = T_1^n + Fo\\left(T_2^n + 2T_L - 3T_1^n\\right)$$</div>
          <div class="eq">$$T_N^{{n+1}} = T_N^n + Fo\\left(T_{{N-1}}^n + 2T_R - 3T_N^n\\right)$$</div>
          <div class="caption">A interface aceita, de forma independente, entrada por $N_x$ ou $\\Delta x$ e por $N_t$ ou $\\Delta t$.</div>
          <div class="caption">Os campos de contorno apresentados ao usuario dependem do modelo de contorno escolhido.</div>
          <div class="caption">O grafico permite comparar mais de um metodo e usar o scroll para avancar no tempo.</div>
          <div class="caption">O esquema atual exige $Fo \\le 0.5$ para estabilidade.</div>
        </div>
      </body>
    </html>
    """
