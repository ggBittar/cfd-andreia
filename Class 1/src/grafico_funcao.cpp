#include "grafico_funcao.hpp"

#include <QPaintEvent>
#include <QPainter>
#include <QPainterPath>
#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

namespace {
constexpr int margem_esquerda = 52;
constexpr int margem_direita = 20;
constexpr int margem_superior = 20;
constexpr int margem_inferior = 36;
constexpr int quantidade_linhas_grade = 8;

bool valor_finito(double valor)
{
    return std::isfinite(valor);
}
}

GraficoFuncao::GraficoFuncao(QWidget* pai)
    : QWidget(pai)
{
    setMinimumHeight(260);
    setAutoFillBackground(true);
    setMouseTracking(true);
}

void GraficoFuncao::definir_modelo(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, std::vector<TrajetoriaMetodo> trajetorias)
{
    modelo_catalogado_ = modelo_catalogado;
    valor_inicial_em_zero_ = valor_inicial_em_zero;
    tempo_inicial_ = tempo_inicial;
    tempo_final_ = tempo_final;
    trajetorias_ = std::move(trajetorias);
    possui_modelo_ = true;
    mensagem_.clear();
    redefinir_zoom();
    update();
}

void GraficoFuncao::definir_mensagem(const QString& mensagem)
{
    mensagem_ = mensagem;
    possui_modelo_ = false;
    zoom_personalizado_ = false;
    update();
}

void GraficoFuncao::paintEvent(QPaintEvent* evento)
{
    Q_UNUSED(evento);

    QPainter pintor(this);
    pintor.setRenderHint(QPainter::Antialiasing, true);
    pintor.fillRect(rect(), QColor(20, 24, 31));

    const QRectF area = area_do_grafico();

    pintor.setPen(QColor(58, 66, 84));
    pintor.drawRoundedRect(area.adjusted(-1, -1, 1, 1), 10, 10);

    if (!mensagem_.isEmpty()) {
        pintor.setPen(QColor(226, 149, 120));
        pintor.drawText(area, Qt::AlignCenter | Qt::TextWordWrap, mensagem_);
        return;
    }

    if (!possui_modelo_) {
        pintor.setPen(QColor(160, 171, 190));
        pintor.drawText(area, Qt::AlignCenter, "Nenhum modelo selecionado.");
        return;
    }

    double x_minimo = 0.0;
    double x_maximo = 0.0;
    double y_minimo = 0.0;
    double y_maximo = 0.0;
    recalcular_limites_automaticos(x_minimo, x_maximo, y_minimo, y_maximo);

    if (!valor_finito(y_minimo) || !valor_finito(y_maximo) || !valor_finito(x_minimo) || !valor_finito(x_maximo)) {
        pintor.setPen(QColor(226, 149, 120));
        pintor.drawText(area, Qt::AlignCenter, "Nao foi possivel desenhar a solucao exata nessa faixa.");
        return;
    }

    desenhar_grade(pintor, area, x_minimo, x_maximo, y_minimo, y_maximo);
    desenhar_eixos(pintor, area, x_minimo, x_maximo, y_minimo, y_maximo);
    desenhar_curva(pintor, area, x_minimo, x_maximo, y_minimo, y_maximo);
    desenhar_trajetorias(pintor, area, x_minimo, x_maximo, y_minimo, y_maximo);
    desenhar_legenda(pintor, area);

    pintor.setPen(QColor(214, 220, 230));
    pintor.drawText(
        QRectF(area.left(), 4, area.width(), 18),
        Qt::AlignCenter,
        QString("%1 | %2").arg(modelo_catalogado_.expressao_funcao).arg(modelo_catalogado_.expressao_derivada)
    );
}

QRectF GraficoFuncao::area_do_grafico() const
{
    return QRectF(
        margem_esquerda,
        margem_superior,
        std::max(120, width() - margem_esquerda - margem_direita),
        std::max(120, height() - margem_superior - margem_inferior)
    );
}

QPointF GraficoFuncao::mapear_para_tela(double x, double y, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo) const
{
    const double x_normalizado = (x - x_minimo) / (x_maximo - x_minimo);
    const double y_normalizado = (y - y_minimo) / (y_maximo - y_minimo);

    return QPointF(
        area.left() + x_normalizado * area.width(),
        area.bottom() - y_normalizado * area.height()
    );
}

double GraficoFuncao::mapear_para_modelo_x(double x_tela, const QRectF& area, double x_minimo, double x_maximo) const
{
    const double proporcao = (x_tela - area.left()) / area.width();
    return x_minimo + proporcao * (x_maximo - x_minimo);
}

void GraficoFuncao::recalcular_limites_automaticos(double& x_minimo, double& x_maximo, double& y_minimo, double& y_maximo) const
{
    if (zoom_personalizado_) {
        x_minimo = x_minimo_visivel_;
        x_maximo = x_maximo_visivel_;
        y_minimo = y_minimo_visivel_;
        y_maximo = y_maximo_visivel_;
        return;
    }

    const double menor_tempo = std::min(tempo_inicial_, tempo_final_);
    const double maior_tempo = std::max(tempo_inicial_, tempo_final_);
    const double margem_horizontal = std::max(0.5, (maior_tempo - menor_tempo) * 0.2);
    x_minimo = menor_tempo - margem_horizontal;
    x_maximo = maior_tempo + margem_horizontal;

    y_minimo = std::numeric_limits<double>::infinity();
    y_maximo = -std::numeric_limits<double>::infinity();

    for (int indice = 0; indice <= 240; ++indice) {
        const double x = x_minimo + (x_maximo - x_minimo) * static_cast<double>(indice) / 240.0;
        const double y = modelo_catalogado_.funcao_exata(valor_inicial_em_zero_, x);

        if (!valor_finito(y)) {
            continue;
        }

        y_minimo = std::min(y_minimo, y);
        y_maximo = std::max(y_maximo, y);
    }

    for (const TrajetoriaMetodo& trajetoria : trajetorias_) {
        for (const PontoSimulacao& ponto : trajetoria.pontos) {
            if (!valor_finito(ponto.valor)) {
                continue;
            }
            y_minimo = std::min(y_minimo, ponto.valor);
            y_maximo = std::max(y_maximo, ponto.valor);
        }
    }

    if (std::abs(y_maximo - y_minimo) < 1e-9) {
        y_minimo -= 1.0;
        y_maximo += 1.0;
    } else {
        const double margem_vertical = (y_maximo - y_minimo) * 0.15;
        y_minimo -= margem_vertical;
        y_maximo += margem_vertical;
    }
}

void GraficoFuncao::redefinir_zoom()
{
    zoom_personalizado_ = false;
    recalcular_limites_automaticos(x_minimo_visivel_, x_maximo_visivel_, y_minimo_visivel_, y_maximo_visivel_);
}

void GraficoFuncao::wheelEvent(QWheelEvent* evento)
{
    if (!possui_modelo_ || !mensagem_.isEmpty()) {
        evento->ignore();
        return;
    }

    const QRectF area = area_do_grafico();
    if (!area.contains(evento->position())) {
        evento->ignore();
        return;
    }

    double x_minimo = 0.0;
    double x_maximo = 0.0;
    double y_minimo = 0.0;
    double y_maximo = 0.0;
    recalcular_limites_automaticos(x_minimo, x_maximo, y_minimo, y_maximo);

    const double fator = evento->angleDelta().y() > 0 ? 0.85 : 1.15;
    const double centro_x = mapear_para_modelo_x(evento->position().x(), area, x_minimo, x_maximo);
    const double centro_y = y_maximo - ((evento->position().y() - area.top()) / area.height()) * (y_maximo - y_minimo);

    const double nova_largura = std::max(0.001, (x_maximo - x_minimo) * fator);
    const double nova_altura = std::max(0.001, (y_maximo - y_minimo) * fator);

    const double proporcao_x = (centro_x - x_minimo) / (x_maximo - x_minimo);
    const double proporcao_y = (centro_y - y_minimo) / (y_maximo - y_minimo);

    x_minimo_visivel_ = centro_x - proporcao_x * nova_largura;
    x_maximo_visivel_ = x_minimo_visivel_ + nova_largura;
    y_minimo_visivel_ = centro_y - proporcao_y * nova_altura;
    y_maximo_visivel_ = y_minimo_visivel_ + nova_altura;
    zoom_personalizado_ = true;

    update();
    evento->accept();
}

void GraficoFuncao::mouseDoubleClickEvent(QMouseEvent* evento)
{
    if (evento->button() == Qt::LeftButton) {
        redefinir_zoom();
        update();
        evento->accept();
        return;
    }

    QWidget::mouseDoubleClickEvent(evento);
}

void GraficoFuncao::desenhar_grade(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo)
{
    QPen caneta_grade(QColor(44, 50, 63));
    caneta_grade.setWidth(1);
    pintor.setPen(caneta_grade);

    for (int indice = 0; indice <= quantidade_linhas_grade; ++indice) {
        const double proporcao = static_cast<double>(indice) / quantidade_linhas_grade;
        const double x = area.left() + proporcao * area.width();
        const double y = area.top() + proporcao * area.height();

        pintor.drawLine(QPointF(x, area.top()), QPointF(x, area.bottom()));
        pintor.drawLine(QPointF(area.left(), y), QPointF(area.right(), y));

        const double valor_x = x_minimo + proporcao * (x_maximo - x_minimo);
        const double valor_y = y_maximo - proporcao * (y_maximo - y_minimo);

        pintor.setPen(QColor(130, 141, 160));
        pintor.drawText(QRectF(x - 28, area.bottom() + 6, 56, 16), Qt::AlignCenter, QString::number(valor_x, 'g', 4));
        pintor.drawText(QRectF(4, y - 8, margem_esquerda - 10, 16), Qt::AlignRight | Qt::AlignVCenter, QString::number(valor_y, 'g', 4));
        pintor.setPen(caneta_grade);
    }
}

void GraficoFuncao::desenhar_eixos(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo)
{
    QPen caneta_eixos(QColor(115, 132, 158));
    caneta_eixos.setWidth(2);
    pintor.setPen(caneta_eixos);

    if (x_minimo <= 0.0 && x_maximo >= 0.0) {
        const QPointF origem_superior = mapear_para_tela(0.0, y_maximo, area, x_minimo, x_maximo, y_minimo, y_maximo);
        const QPointF origem_inferior = mapear_para_tela(0.0, y_minimo, area, x_minimo, x_maximo, y_minimo, y_maximo);
        pintor.drawLine(origem_superior, origem_inferior);
    }

    if (y_minimo <= 0.0 && y_maximo >= 0.0) {
        const QPointF origem_esquerda = mapear_para_tela(x_minimo, 0.0, area, x_minimo, x_maximo, y_minimo, y_maximo);
        const QPointF origem_direita = mapear_para_tela(x_maximo, 0.0, area, x_minimo, x_maximo, y_minimo, y_maximo);
        pintor.drawLine(origem_esquerda, origem_direita);
    }
}

void GraficoFuncao::desenhar_curva(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo)
{
    QPen caneta_curva(QColor(84, 191, 160));
    caneta_curva.setWidth(3);
    pintor.setPen(caneta_curva);

    QPainterPath caminho;
    bool segmento_ativo = false;

    for (int pixel = 0; pixel <= static_cast<int>(area.width()); ++pixel) {
        const double proporcao = area.width() <= 0.0 ? 0.0 : static_cast<double>(pixel) / area.width();
        const double x = x_minimo + proporcao * (x_maximo - x_minimo);
        const double y = modelo_catalogado_.funcao_exata(valor_inicial_em_zero_, x);

        if (!valor_finito(y) || y < y_minimo - (y_maximo - y_minimo) * 3.0 || y > y_maximo + (y_maximo - y_minimo) * 3.0) {
            segmento_ativo = false;
            continue;
        }

        const QPointF ponto = mapear_para_tela(x, y, area, x_minimo, x_maximo, y_minimo, y_maximo);
        if (!segmento_ativo) {
            caminho.moveTo(ponto);
            segmento_ativo = true;
        } else {
            caminho.lineTo(ponto);
        }
    }

    pintor.drawPath(caminho);
}

void GraficoFuncao::desenhar_trajetorias(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo)
{
    for (const TrajetoriaMetodo& trajetoria : trajetorias_) {
        if (trajetoria.pontos.size() < 2) {
            continue;
        }

        QPen caneta(trajetoria.cor);
        caneta.setWidth(2);
        caneta.setStyle(Qt::DashLine);
        pintor.setPen(caneta);

        QPainterPath caminho;
        bool primeiro = true;

        for (const PontoSimulacao& ponto_simulacao : trajetoria.pontos) {
            const QPointF ponto = mapear_para_tela(
                ponto_simulacao.tempo,
                ponto_simulacao.valor,
                area,
                x_minimo,
                x_maximo,
                y_minimo,
                y_maximo
            );

            if (primeiro) {
                caminho.moveTo(ponto);
                primeiro = false;
            } else {
                caminho.lineTo(ponto);
            }
        }

        pintor.drawPath(caminho);
    }
}

void GraficoFuncao::desenhar_intervalo_destacado(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo)
{
    Q_UNUSED(pintor);
    Q_UNUSED(area);
    Q_UNUSED(x_minimo);
    Q_UNUSED(x_maximo);
    Q_UNUSED(y_minimo);
    Q_UNUSED(y_maximo);
}

void GraficoFuncao::desenhar_legenda(QPainter& pintor, const QRectF& area)
{
    const QRectF caixa_legenda(area.right() - 170, area.top() + 10, 160, 110);
    pintor.setPen(QColor(58, 66, 84));
    pintor.setBrush(QColor(16, 20, 26, 210));
    pintor.drawRoundedRect(caixa_legenda, 8, 8);

    int linha = 0;
    auto desenhar_item = [&](const QString& nome, const QColor& cor) {
        const qreal y = caixa_legenda.top() + 14 + (linha * 22);
        pintor.setPen(QPen(cor, 2));
        pintor.drawLine(QPointF(caixa_legenda.left() + 10, y), QPointF(caixa_legenda.left() + 28, y));
        pintor.setPen(QColor(230, 235, 242));
        pintor.drawText(QRectF(caixa_legenda.left() + 34, y - 9, caixa_legenda.width() - 40, 18), Qt::AlignLeft | Qt::AlignVCenter, nome);
        ++linha;
    };

    desenhar_item("Exata", QColor(84, 191, 160));
    for (const TrajetoriaMetodo& trajetoria : trajetorias_) {
        desenhar_item(trajetoria.nome_metodo, trajetoria.cor);
    }
}
