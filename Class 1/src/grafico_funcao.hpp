#pragma once

#include "aproximacoes.hpp"

#include <QMouseEvent>
#include <QWheelEvent>
#include <QWidget>

class GraficoFuncao : public QWidget
{
public:
    explicit GraficoFuncao(QWidget* pai = nullptr);

    void definir_modelo(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, std::vector<TrajetoriaMetodo> trajetorias);
    void definir_mensagem(const QString& mensagem);

protected:
    void paintEvent(QPaintEvent* evento) override;
    void wheelEvent(QWheelEvent* evento) override;
    void mouseDoubleClickEvent(QMouseEvent* evento) override;

private:
    QRectF area_do_grafico() const;
    QPointF mapear_para_tela(double x, double y, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo) const;
    double mapear_para_modelo_x(double x_tela, const QRectF& area, double x_minimo, double x_maximo) const;
    void recalcular_limites_automaticos(double& x_minimo, double& x_maximo, double& y_minimo, double& y_maximo) const;
    void redefinir_zoom();
    void desenhar_grade(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo);
    void desenhar_eixos(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo);
    void desenhar_curva(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo);
    void desenhar_trajetorias(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo);
    void desenhar_intervalo_destacado(QPainter& pintor, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo);
    void desenhar_legenda(QPainter& pintor, const QRectF& area);

    bool possui_modelo_ = false;
    ModeloCatalogado modelo_catalogado_;
    double valor_inicial_em_zero_ = 1.0;
    double tempo_inicial_ = 0.0;
    double tempo_final_ = 0.0;
    std::vector<TrajetoriaMetodo> trajetorias_;
    QString mensagem_;
    bool zoom_personalizado_ = false;
    double x_minimo_visivel_ = 0.0;
    double x_maximo_visivel_ = 1.0;
    double y_minimo_visivel_ = -1.0;
    double y_maximo_visivel_ = 1.0;
};
