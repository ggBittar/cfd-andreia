#include "functioncatalog.h"

#include <cmath>
#include <QStringList>

double phi_n(double x, double t, int n, double c = 4.0, double ni = 1.0)
{
    const double shiftedX = x - c * t - (2 * n + 1) * M_PI;
    return std::exp(-(shiftedX * shiftedX) / (4 * ni * (t + 1)));
}

double phi_x_n(double x, double t, int n, double c = 4.0, double ni = 1.0)
{
    const double shiftedX = x - c * t - (2 * n + 1) * M_PI;
    return (-(shiftedX) / (2 * ni * (t + 1))) * std::exp(-(shiftedX * shiftedX) / (4 * ni * (t + 1)));
}

double phi(double x, double t, int N, double c = 4.0, double ni = 1.0)
{
    double sum = 0.0;
    for (int n = -N; n <= N; ++n) {
        sum += phi_n(x, t, n, c, ni);
    }
    return sum;
}

double phi_x(double x, double t, int N, double c = 4.0, double ni = 1.0)
{
    double sum = 0.0;
    for (int n = -N; n <= N; ++n) {
        sum += phi_x_n(x, t, n, c, ni);
    }
    return sum;
}


namespace {
double exponentialSum(double x, double t, int N)
{
    
    double c = 4.0;
    double ni = 1.0;
    return c -2*ni * (phi_x(x, t, N, c, ni) / phi(x, t, N, c, ni));
    
}
}

const QList<NamedFunction> &availableFunctions()
{
    static const QList<NamedFunction> functions = {
        {
            "exp_sum",
            "Solucao em funcao de Phi",
            "u(x, t, N) = c - 2 nu Phi_x(x, t, N) / Phi(x, t, N)",
            exponentialSum
        }
    };

    return functions;
}

NamedFunction findFunctionById(const QString &id)
{
    for (const NamedFunction &function : availableFunctions()) {
        if (function.id == id) {
            return function;
        }
    }

    return {};
}

QString formulationsHtml()
{
    return QString(
        "<html>"
        "<head>"
        "<meta charset='utf-8'>"
        "<style>"
        "body { font-family: 'Segoe UI', sans-serif; color: #1f2933; background: #f8fafc; margin: 18px; }"
        "h1, h2 { color: #102a43; }"
        ".card { background: white; border: 1px solid #d9e2ec; border-radius: 10px; padding: 16px; margin-bottom: 16px; }"
        ".eq { font-family: 'Cambria Math', 'Times New Roman', serif; font-size: 22px; padding: 8px 0; color: #243b53; text-align: center; }"
        ".caption { color: #486581; margin-bottom: 10px; }"
        ".frac { display: inline-block; vertical-align: middle; text-align: center; line-height: 1.2; margin: 0 4px; }"
        ".frac .top { display: block; padding: 0 8px 2px 8px; border-bottom: 1px solid #243b53; }"
        ".frac .bottom { display: block; padding: 2px 8px 0 8px; }"
        ".sum { display: inline-block; position: relative; vertical-align: middle; width: 34px; margin: 0 6px; }"
        ".sum .symbol { display: block; font-size: 34px; line-height: 30px; }"
        ".sum .upper { position: absolute; top: -14px; left: 0; right: 0; font-size: 12px; }"
        ".sum .lower { position: absolute; bottom: -16px; left: 0; right: 0; font-size: 12px; }"
        ".mono { font-family: Consolas, monospace; font-size: 14px; color: #486581; margin-top: 8px; text-align: center; }"
        "</style>"
        "</head>"
        "<body>"
        "<h1>Formulações em função de &Phi;</h1>"
        "<div class='card'>"
        "<h2>Função principal</h2>"
        "<div class='caption'>Campo principal escrito a partir de &Phi;.</div>"
        "<div class='eq'>u(x,t,N) = c - 2&nu;"
        "<span class='frac'><span class='top'>&phi;<sub>x</sub>(x,t,N)</span><span class='bottom'>/&phi;(x,t,N)</span></span>"
        "</div>"
        "<div class='mono'>u(x,t,N) = c - 2 nu phi_x(x,t,N) / phi(x,t,N)</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Função auxiliar &Phi;</h2>"
        "<div class='caption'>Definição compacta da função auxiliar.</div>"
        "<div class='eq'>&phi;(x,t,N) = "
        "<span class='sum'><span class='upper'>N</span><span class='symbol'>&sum;</span><span class='lower'>n = -N</span></span>"
        "&phi;<sub>n</sub>(x,t,n)</div>"
        "<div class='mono'>phi(x,t,N) = sum from n=-N to N of phi_n(x,t,n)</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Derivada espacial &Phi;<sub>x</sub></h2>"
        "<div class='caption'>Derivada espacial da função auxiliar.</div>"
        "<div class='eq'>&phi;<sub>x</sub>(x,t,N) = "
        "<span class='sum'><span class='upper'>N</span><span class='symbol'>&sum;</span><span class='lower'>n = -N</span></span>"
        "&phi;<sub>x,n</sub>(x,t,n)</div>"
        "<div class='mono'>phi_x(x,t,N) = sum from n=-N to N of phi_x_n(x,t,n)</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Termo elemental &phi;<sub>n</sub></h2>"
        "<div class='caption'>Contribuição individual de cada modo.</div>"
        "<div class='eq'>&phi;<sub>n</sub>(x,t,n) = exp("
        "-<span class='frac'>"
        "<span class='top'>(x - ct - (2n + 1)&pi;)<sup>2</sup></span>"
        "<span class='bottom'>/4&nu;(t + 1)</span>"
        "</span>)</div>"
        "<div class='mono'>phi_n(x,t,n) = exp(-(x - ct - (2n + 1)pi)^2 / (4 nu (t + 1)))</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Derivada do termo elemental &phi;<sub>x,n</sub></h2>"
        "<div class='caption'>Derivada espacial do termo elemental.</div>"
        "<div class='eq'>&phi;<sub>x,n</sub>(x,t,n) = "
        "-<span class='frac'>"
        "<span class='top'>x - ct - (2n + 1)&pi;</span>"
        "<span class='bottom'>/2&nu;(t + 1)</span>"
        "</span>"
        "exp("
        "-<span class='frac'>"
        "<span class='top'>(x - ct - (2n + 1)&pi;)<sup>2</sup></span>"
        "<span class='bottom'>/4&nu;(t + 1)</span>"
        "</span>)</div>"
        "<div class='mono'>phi_x_n(x,t,n) = -(x - ct - (2n + 1)pi)/(2 nu (t + 1)) * exp(-(x - ct - (2n + 1)pi)^2/(4 nu (t + 1)))</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Parâmetros atuais do backend</h2>"
        "<div class='eq'>c = 4.0,&nbsp;&nbsp;&nbsp;&nu; = 1.0</div>"
        "</div>"
        "</body>"
        "</html>");
}

QString formulationsMathJaxHtml()
{
    return QString(
        "<html>"
        "<head>"
        "<meta charset='utf-8'>"
        "<script>"
        "window.MathJax = {"
        "tex: {"
        "inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],"
        "displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]"
        "},"
        "svg: { fontCache: 'global' }"
        "};"
        "</script>"
        "<script async src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'></script>"
        "<style>"
        "body { font-family: 'Segoe UI', sans-serif; color: #1f2933; background: #f8fafc; margin: 18px; }"
        "h1, h2 { color: #102a43; }"
        ".card { background: white; border: 1px solid #d9e2ec; border-radius: 10px; padding: 16px; margin-bottom: 16px; }"
        ".eq { font-size: 18px; padding: 8px 0; color: #243b53; overflow-x: auto; }"
        ".caption { color: #486581; margin-bottom: 10px; }"
        ".mono { font-family: Consolas, monospace; font-size: 14px; color: #486581; margin-top: 8px; }"
        "</style>"
        "</head>"
        "<body>"
        "<h1>Formulações em função de \\Phi</h1>"
        "<div class='card'>"
        "<h2>Função principal</h2>"
        "<div class='caption'>Campo principal escrito a partir de \\Phi.</div>"
        "<div class='eq'>$$u(x,t,N) = c - 2\\nu \\frac{\\phi_x(x,t,N)}{\\phi(x,t,N)}$$</div>"
        "<div class='mono'>u(x,t,N) = c - 2 nu phi_x(x,t,N) / phi(x,t,N)</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Função auxiliar \\Phi</h2>"
        "<div class='caption'>Definição compacta da função auxiliar.</div>"
        "<div class='eq'>$$\\phi(x,t,N) = \\sum_{n=-N}^{N} \\phi_n(x,t,n)$$</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Derivada espacial \\Phi_x</h2>"
        "<div class='caption'>Derivada espacial da função auxiliar.</div>"
        "<div class='eq'>$$\\phi_x(x,t,N) = \\sum_{n=-N}^{N} \\phi_{x,n}(x,t,n)$$</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Termo elemental \\phi_n</h2>"
        "<div class='caption'>Contribuição individual de cada modo.</div>"
        "<div class='eq'>$$\\phi_n(x,t,n) = \\exp\\left(-\\frac{(x - ct - (2n + 1)\\pi)^2}{4\\nu(t+1)}\\right)$$</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Derivada do termo elemental \\phi_{x,n}</h2>"
        "<div class='caption'>Derivada espacial do termo elemental.</div>"
        "<div class='eq'>$$\\phi_{x,n}(x,t,n) = -\\frac{x - ct - (2n + 1)\\pi}{2\\nu(t+1)}\\exp\\left(-\\frac{(x - ct - (2n + 1)\\pi)^2}{4\\nu(t+1)}\\right)$$</div>"
        "</div>"
        "<div class='card'>"
        "<h2>Parâmetros atuais do backend</h2>"
        "<div class='eq'>$$c = 4.0, \\quad \\nu = 1.0$$</div>"
        "</div>"
        "</body>"
        "</html>");
}
