#pragma once

#include "aproximacoes.hpp"
#include "grafico_funcao.hpp"

#include <QComboBox>
#include <QDoubleSpinBox>
#include <QLabel>
#include <QMainWindow>
#include <QTableWidget>
#include <QTabWidget>
#include <vector>

class JanelaPrincipal : public QMainWindow
{
public:
    explicit JanelaPrincipal(QWidget* pai = nullptr);

private:
    void atualizar_avaliacao();
    void configurar_interface();
    void preencher_modelos();
    void atualizar_resumo(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta);
    void preencher_tabela(const std::vector<ResultadoMetodo>& resultados);

    std::vector<ModeloCatalogado> catalogo_de_modelos_;
    QComboBox* seletor_de_modelo_ = nullptr;
    QDoubleSpinBox* campo_valor_inicial_ = nullptr;
    QDoubleSpinBox* campo_tempo_inicial_ = nullptr;
    QDoubleSpinBox* campo_tempo_final_ = nullptr;
    QDoubleSpinBox* campo_delta_t_ = nullptr;
    QDoubleSpinBox* campo_theta_ = nullptr;
    QLabel* rotulo_expressao_ = nullptr;
    QLabel* rotulo_resumo_ = nullptr;
    GraficoFuncao* grafico_funcao_ = nullptr;
    QTableWidget* tabela_resultados_ = nullptr;
    QTabWidget* abas_principais_ = nullptr;
};
