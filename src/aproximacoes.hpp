#pragma once

#include <functional>
#include <optional>
#include <QColor>
#include <QString>
#include <QPointF>
#include <vector>

struct ModeloCatalogado {
    QString nome;
    QString descricao;
    QString expressao;
    double coeficiente_lambda;
};

struct ResultadoMetodo {
    QString nome_metodo;
    double valor_aproximado;
    double valor_exato;
    double erro_absoluto;
};

struct PontoSimulacao {
    double tempo;
    double valor;
};

struct TrajetoriaMetodo {
    QString nome_metodo;
    QColor cor;
    std::vector<PontoSimulacao> pontos;
};

struct ResumoSimulacaoTheta {
    double tempo_inicial;
    double tempo_final;
    double delta_t_efetivo;
    int quantidade_passos;
    double valor_inicial_em_zero;
    double valor_inicial_no_tempo;
    double valor_exato;
};

double avancar_metodo_theta(double valor_atual, double coeficiente_lambda, double delta_t, double theta);
double calcular_solucao_pelo_metodo_theta(double valor_inicial, double coeficiente_lambda, double tempo_inicial, double tempo_final, double delta_t, double theta, int& quantidade_passos, double& delta_t_efetivo);
double calcular_solucao_exata(double valor_inicial_em_zero, double coeficiente_lambda, double tempo);
TrajetoriaMetodo calcular_trajetoria_pelo_metodo_theta(const QString& nome_metodo, const QColor& cor, double valor_inicial, double coeficiente_lambda, double tempo_inicial, double tempo_final, double delta_t, double theta);

std::vector<ModeloCatalogado> criar_catalogo_de_modelos();
std::vector<ResultadoMetodo> calcular_resultados(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta_usuario);
ResumoSimulacaoTheta calcular_resumo_da_simulacao(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t);
std::optional<QString> validar_parametros_do_modelo(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta);
std::vector<TrajetoriaMetodo> calcular_trajetorias(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta_usuario);
