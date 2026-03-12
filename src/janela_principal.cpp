#include "janela_principal.hpp"

#include <QFormLayout>
#include <QHeaderView>
#include <QLabel>
#include <QSplitter>
#include <QTabWidget>
#include <QVBoxLayout>
#include <QWidget>

JanelaPrincipal::JanelaPrincipal(QWidget* pai)
    : QMainWindow(pai),
      catalogo_de_modelos_(criar_catalogo_de_modelos())
{
    configurar_interface();
    preencher_modelos();
    atualizar_avaliacao();
}

void JanelaPrincipal::configurar_interface()
{
    setWindowTitle("Avaliador de Aproximacoes de Derivadas");
    resize(920, 560);

    auto* widget_central = new QWidget(this);
    auto* layout_principal = new QVBoxLayout(widget_central);
    layout_principal->setContentsMargins(18, 18, 18, 18);
    layout_principal->setSpacing(14);

    auto* titulo = new QLabel("Comparador de Metodos de Aproximacao Numerica", widget_central);
    titulo->setObjectName("titulo_principal");

    auto* subtitulo = new QLabel(
        "Escolha um modelo, defina o tempo final, delta t e o parametro theta para comparar os esquemas temporais.",
        widget_central
    );
    subtitulo->setObjectName("subtitulo_principal");
    subtitulo->setWordWrap(true);

    auto* layout_controles = new QFormLayout();
    layout_controles->setLabelAlignment(Qt::AlignRight);
    layout_controles->setFormAlignment(Qt::AlignLeft | Qt::AlignTop);
    layout_controles->setHorizontalSpacing(12);
    layout_controles->setVerticalSpacing(10);

    seletor_de_modelo_ = new QComboBox(widget_central);

    campo_valor_inicial_ = new QDoubleSpinBox(widget_central);
    campo_valor_inicial_->setDecimals(6);
    campo_valor_inicial_->setRange(-1000000.0, 1000000.0);
    campo_valor_inicial_->setValue(1.0);

    campo_tempo_inicial_ = new QDoubleSpinBox(widget_central);
    campo_tempo_inicial_->setDecimals(6);
    campo_tempo_inicial_->setRange(-1000.0, 1000.0);
    campo_tempo_inicial_->setValue(0.0);

    campo_tempo_final_ = new QDoubleSpinBox(widget_central);
    campo_tempo_final_->setDecimals(6);
    campo_tempo_final_->setRange(-1000.0, 1000.0);
    campo_tempo_final_->setValue(1.0);

    campo_delta_t_ = new QDoubleSpinBox(widget_central);
    campo_delta_t_->setDecimals(6);
    campo_delta_t_->setRange(0.000001, 100.0);
    campo_delta_t_->setSingleStep(0.001);
    campo_delta_t_->setValue(0.05);

    campo_theta_ = new QDoubleSpinBox(widget_central);
    campo_theta_->setDecimals(3);
    campo_theta_->setRange(0.0, 1.0);
    campo_theta_->setSingleStep(0.05);
    campo_theta_->setValue(0.5);

    layout_controles->addRow("Modelo:", seletor_de_modelo_);
    layout_controles->addRow("u(0):", campo_valor_inicial_);
    layout_controles->addRow("Tempo inicial:", campo_tempo_inicial_);
    layout_controles->addRow("Tempo final:", campo_tempo_final_);
    layout_controles->addRow("Delta t:", campo_delta_t_);
    layout_controles->addRow("Theta:", campo_theta_);

    rotulo_expressao_ = new QLabel(widget_central);
    rotulo_expressao_->setObjectName("rotulo_expressao");
    rotulo_expressao_->setWordWrap(true);

    rotulo_resumo_ = new QLabel(widget_central);
    rotulo_resumo_->setObjectName("rotulo_resumo");
    rotulo_resumo_->setWordWrap(true);

    grafico_funcao_ = new GraficoFuncao(widget_central);

    tabela_resultados_ = new QTableWidget(widget_central);
    tabela_resultados_->setColumnCount(4);
    tabela_resultados_->setHorizontalHeaderLabels({
        "Metodo",
        "Valor numerico",
        "Valor exato",
        "Erro absoluto"
    });
    tabela_resultados_->horizontalHeader()->setStretchLastSection(true);
    tabela_resultados_->horizontalHeader()->setSectionResizeMode(0, QHeaderView::Stretch);
    tabela_resultados_->horizontalHeader()->setSectionResizeMode(1, QHeaderView::ResizeToContents);
    tabela_resultados_->horizontalHeader()->setSectionResizeMode(2, QHeaderView::ResizeToContents);
    tabela_resultados_->horizontalHeader()->setSectionResizeMode(3, QHeaderView::ResizeToContents);
    tabela_resultados_->verticalHeader()->setVisible(false);
    tabela_resultados_->setEditTriggers(QAbstractItemView::NoEditTriggers);
    tabela_resultados_->setSelectionMode(QAbstractItemView::NoSelection);
    tabela_resultados_->setAlternatingRowColors(true);

    auto* pagina_parametros = new QWidget(widget_central);
    auto* layout_parametros = new QVBoxLayout(pagina_parametros);
    layout_parametros->setContentsMargins(0, 0, 0, 0);
    layout_parametros->setSpacing(14);
    layout_parametros->addWidget(titulo);
    layout_parametros->addWidget(subtitulo);
    layout_parametros->addLayout(layout_controles);
    layout_parametros->addWidget(rotulo_expressao_);
    layout_parametros->addWidget(rotulo_resumo_);
    layout_parametros->addStretch(1);

    auto* pagina_resultados = new QWidget(widget_central);
    auto* layout_resultados = new QVBoxLayout(pagina_resultados);
    layout_resultados->setContentsMargins(0, 0, 0, 0);
    layout_resultados->setSpacing(12);
    auto* divisor_conteudo = new QSplitter(Qt::Vertical, pagina_resultados);
    divisor_conteudo->addWidget(grafico_funcao_);
    divisor_conteudo->addWidget(tabela_resultados_);
    divisor_conteudo->setStretchFactor(0, 3);
    divisor_conteudo->setStretchFactor(1, 2);
    layout_resultados->addWidget(divisor_conteudo);

    abas_principais_ = new QTabWidget(widget_central);
    abas_principais_->addTab(pagina_parametros, "Parametros");
    abas_principais_->addTab(pagina_resultados, "Resultados");

    layout_principal->addWidget(abas_principais_, 1);

    setCentralWidget(widget_central);

    connect(seletor_de_modelo_, qOverload<int>(&QComboBox::currentIndexChanged), this, &JanelaPrincipal::atualizar_avaliacao);
    connect(campo_valor_inicial_, qOverload<double>(&QDoubleSpinBox::valueChanged), this, &JanelaPrincipal::atualizar_avaliacao);
    connect(campo_tempo_inicial_, qOverload<double>(&QDoubleSpinBox::valueChanged), this, &JanelaPrincipal::atualizar_avaliacao);
    connect(campo_tempo_final_, qOverload<double>(&QDoubleSpinBox::valueChanged), this, &JanelaPrincipal::atualizar_avaliacao);
    connect(campo_delta_t_, qOverload<double>(&QDoubleSpinBox::valueChanged), this, &JanelaPrincipal::atualizar_avaliacao);
    connect(campo_theta_, qOverload<double>(&QDoubleSpinBox::valueChanged), this, &JanelaPrincipal::atualizar_avaliacao);
}

void JanelaPrincipal::preencher_modelos()
{
    for (const ModeloCatalogado& modelo_catalogado : catalogo_de_modelos_) {
        seletor_de_modelo_->addItem(modelo_catalogado.nome);
    }
}

void JanelaPrincipal::atualizar_avaliacao()
{
    const int indice_atual = seletor_de_modelo_->currentIndex();
    if (indice_atual < 0 || indice_atual >= static_cast<int>(catalogo_de_modelos_.size())) {
        return;
    }

    const ModeloCatalogado& modelo_catalogado = catalogo_de_modelos_.at(indice_atual);
    const double valor_inicial_em_zero = campo_valor_inicial_->value();
    const double tempo_inicial = campo_tempo_inicial_->value();
    const double tempo_final = campo_tempo_final_->value();
    const double delta_t = campo_delta_t_->value();
    const double theta = campo_theta_->value();

    if (const auto validacao = validar_parametros_do_modelo(modelo_catalogado, valor_inicial_em_zero, tempo_inicial, tempo_final, delta_t, theta)) {
        rotulo_expressao_->setText(
            QString("Modelo selecionado: %1 | Derivada analitica: %2")
                .arg(modelo_catalogado.expressao_funcao)
                .arg(modelo_catalogado.expressao_derivada)
        );
        rotulo_resumo_->setText(*validacao);
        grafico_funcao_->definir_mensagem(*validacao);
        tabela_resultados_->setRowCount(0);
        return;
    }

    rotulo_expressao_->setText(
        QString("Modelo selecionado: %1 | Derivada analitica: %2")
            .arg(modelo_catalogado.expressao_funcao)
            .arg(modelo_catalogado.expressao_derivada)
    );
    atualizar_resumo(modelo_catalogado, valor_inicial_em_zero, tempo_inicial, tempo_final, delta_t, theta);
    grafico_funcao_->definir_modelo(
        modelo_catalogado,
        valor_inicial_em_zero,
        tempo_inicial,
        tempo_final,
        calcular_trajetorias(modelo_catalogado, valor_inicial_em_zero, tempo_inicial, tempo_final, delta_t, theta)
    );
    preencher_tabela(calcular_resultados(modelo_catalogado, valor_inicial_em_zero, tempo_inicial, tempo_final, delta_t, theta));
}

void JanelaPrincipal::atualizar_resumo(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta)
{
    const ResumoSimulacaoTheta resumo = calcular_resumo_da_simulacao(modelo_catalogado, valor_inicial_em_zero, tempo_inicial, tempo_final, delta_t);

    rotulo_resumo_->setText(
        QString("%1 u(0) = %2, t inicial = %3, u(t inicial) = %4, t final = %5, delta t efetivo = %6, passos = %7, theta do usuario = %8 e u(t final) exata = %9.")
            .arg(modelo_catalogado.descricao)
            .arg(resumo.valor_inicial_em_zero, 0, 'g', 6)
            .arg(resumo.tempo_inicial, 0, 'g', 8)
            .arg(resumo.valor_inicial_no_tempo, 0, 'g', 10)
            .arg(resumo.tempo_final, 0, 'g', 8)
            .arg(resumo.delta_t_efetivo, 0, 'g', 8)
            .arg(resumo.quantidade_passos)
            .arg(theta, 0, 'g', 4)
            .arg(resumo.valor_exato, 0, 'g', 10)
    );
}

void JanelaPrincipal::preencher_tabela(const std::vector<ResultadoMetodo>& resultados)
{
    tabela_resultados_->setRowCount(static_cast<int>(resultados.size()));

    for (int linha = 0; linha < static_cast<int>(resultados.size()); ++linha) {
        const ResultadoMetodo& resultado = resultados.at(linha);

        // A tabela destaca lado a lado aproximacao, valor exato e erro absoluto.
        tabela_resultados_->setItem(linha, 0, new QTableWidgetItem(resultado.nome_metodo));
        tabela_resultados_->setItem(linha, 1, new QTableWidgetItem(QString::number(resultado.valor_aproximado, 'g', 12)));
        tabela_resultados_->setItem(linha, 2, new QTableWidgetItem(QString::number(resultado.valor_exato, 'g', 12)));
        tabela_resultados_->setItem(linha, 3, new QTableWidgetItem(QString::number(resultado.erro_absoluto, 'g', 12)));
    }

    tabela_resultados_->resizeRowsToContents();
}
