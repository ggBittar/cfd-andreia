#pragma once

#include "aproximacoes.hpp"

#include <QWidget>

class GraficoFuncao : public QWidget
{
public:
    explicit GraficoFuncao(QWidget* pai = nullptr);

    void definir_modelo(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, std::vector<TrajetoriaMetodo> trajetorias);
    void definir_mensagem(const QString& mensagem);

protected:
    void paintEvent(QPaintEvent* evento) override;

private:
    QRectF area_do_grafico() const;
    QPointF mapear_para_tela(double x, double y, const QRectF& area, double x_minimo, double x_maximo, double y_minimo, double y_maximo) const;
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
};
