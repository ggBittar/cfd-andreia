#include "aproximacoes.hpp"

#include <algorithm>
#include <cmath>

namespace {
double calcular_erro_absoluto(double valor_aproximado, double valor_exato)
{
    return std::abs(valor_aproximado - valor_exato);
}

double limitar_theta(double theta)
{
    return std::clamp(theta, 0.0, 1.0);
}
}

double avancar_metodo_theta(double valor_atual, double coeficiente_lambda, double delta_t, double theta)
{
    const double theta_limitado = limitar_theta(theta);
    const double numerador = valor_atual * (1.0 + (1.0 - theta_limitado) * coeficiente_lambda * delta_t);
    const double denominador = 1.0 - theta_limitado * coeficiente_lambda * delta_t;

    return numerador / denominador;
}

double calcular_solucao_pelo_metodo_theta(double valor_inicial, double coeficiente_lambda, double tempo_inicial, double tempo_final, double delta_t, double theta, int& quantidade_passos, double& delta_t_efetivo)
{
    const double intervalo_total = tempo_final - tempo_inicial;
    double valor_atual = valor_inicial;
    const double direcao = intervalo_total >= 0.0 ? 1.0 : -1.0;
    const double delta_t_assinado = direcao * delta_t;
    const double duracao_total = std::abs(intervalo_total);
    const int quantidade_passos_completos = static_cast<int>(std::floor(duracao_total / delta_t));
    const double duracao_restante = duracao_total - (static_cast<double>(quantidade_passos_completos) * delta_t);

    quantidade_passos = quantidade_passos_completos;
    for (int passo = 0; passo < quantidade_passos_completos; ++passo) {
        valor_atual = avancar_metodo_theta(valor_atual, coeficiente_lambda, delta_t_assinado, theta);
    }

    if (duracao_restante > 1e-12) {
        valor_atual = avancar_metodo_theta(valor_atual, coeficiente_lambda, direcao * duracao_restante, theta);
        ++quantidade_passos;
    }

    if (quantidade_passos == 0) {
        valor_atual = avancar_metodo_theta(valor_atual, coeficiente_lambda, intervalo_total, theta);
        quantidade_passos = 1;
        delta_t_efetivo = intervalo_total;
        return valor_atual;
    }

    delta_t_efetivo = quantidade_passos_completos > 0 ? delta_t_assinado : intervalo_total;
    return valor_atual;
}

double calcular_solucao_exata(double valor_inicial_em_zero, double coeficiente_lambda, double tempo)
{
    return valor_inicial_em_zero * std::exp(coeficiente_lambda * tempo);
}

TrajetoriaMetodo calcular_trajetoria_pelo_metodo_theta(const QString& nome_metodo, const QColor& cor, double valor_inicial, double coeficiente_lambda, double tempo_inicial, double tempo_final, double delta_t, double theta)
{
    TrajetoriaMetodo trajetoria{nome_metodo, cor, {{tempo_inicial, valor_inicial}}};

    const double intervalo_total = tempo_final - tempo_inicial;
    const double direcao = intervalo_total >= 0.0 ? 1.0 : -1.0;
    const double delta_t_assinado = direcao * delta_t;
    const double duracao_total = std::abs(intervalo_total);
    const int quantidade_passos_completos = static_cast<int>(std::floor(duracao_total / delta_t));
    const double duracao_restante = duracao_total - (static_cast<double>(quantidade_passos_completos) * delta_t);

    double tempo_atual = tempo_inicial;
    double valor_atual = valor_inicial;

    for (int passo = 0; passo < quantidade_passos_completos; ++passo) {
        valor_atual = avancar_metodo_theta(valor_atual, coeficiente_lambda, delta_t_assinado, theta);
        tempo_atual += delta_t_assinado;
        trajetoria.pontos.push_back({tempo_atual, valor_atual});
    }

    if (duracao_restante > 1e-12) {
        const double ultimo_passo = direcao * duracao_restante;
        valor_atual = avancar_metodo_theta(valor_atual, coeficiente_lambda, ultimo_passo, theta);
        tempo_atual += ultimo_passo;
        trajetoria.pontos.push_back({tempo_atual, valor_atual});
    } else if (quantidade_passos_completos == 0) {
        valor_atual = avancar_metodo_theta(valor_atual, coeficiente_lambda, intervalo_total, theta);
        tempo_atual = tempo_final;
        trajetoria.pontos.push_back({tempo_atual, valor_atual});
    }

    return trajetoria;
}

std::vector<ModeloCatalogado> criar_catalogo_de_modelos()
{
    return {
        {
            "Crescimento Exponencial",
            "Modelo teste com crescimento suave.",
            "u'(t) = 1.0 * u(t), u(0) = 1.0, u(t) = e^t",
            1.0
        },
        {
            "Decaimento Exponencial",
            "Modelo teste com relaxacao unitria.",
            "u'(t) = -1.0 * u(t), u(0) = 1.0, u(t) = e^(-t)",
            -1.0
        },
        {
            "Decaimento Rigido",
            "Modelo teste mais rigido para observar estabilidade numerica.",
            "u'(t) = -10.0 * u(t), u(0) = 1.0, u(t) = e^(-10t)",
            -10.0
        },
        {
            "Crescimento com Escala",
            "Modelo teste com valor inicial diferente de um.",
            "u'(t) = 2.0 * u(t), u(0) = 0.5, u(t) = 0.5e^(2t)",
            2.0
        }
    };
}

std::vector<ResultadoMetodo> calcular_resultados(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta_usuario)
{
    const double valor_inicial_no_tempo = calcular_solucao_exata(valor_inicial_em_zero, modelo_catalogado.coeficiente_lambda, tempo_inicial);
    const double valor_exato = calcular_solucao_exata(valor_inicial_em_zero, modelo_catalogado.coeficiente_lambda, tempo_final);

    std::vector<ResultadoMetodo> resultados;
    resultados.reserve(4);

    const auto adicionar_resultado = [&](const QString& nome_metodo, double theta) {
        int quantidade_passos = 0;
        double delta_t_efetivo = 0.0;
        const double valor_aproximado = calcular_solucao_pelo_metodo_theta(
            valor_inicial_no_tempo,
            modelo_catalogado.coeficiente_lambda,
            tempo_inicial,
            tempo_final,
            delta_t,
            theta,
            quantidade_passos,
            delta_t_efetivo
        );

        resultados.push_back({
            nome_metodo,
            valor_aproximado,
            valor_exato,
            calcular_erro_absoluto(valor_aproximado, valor_exato)
        });
    };

    adicionar_resultado("Metodo explicito (theta = 0)", 0.0);
    adicionar_resultado("Metodo semi-implicito (theta = 0.5)", 0.5);
    adicionar_resultado("Metodo implicito (theta = 1)", 1.0);
    adicionar_resultado(QString("Metodo theta geral (theta = %1)").arg(theta_usuario, 0, 'g', 4), theta_usuario);

    return resultados;
}

ResumoSimulacaoTheta calcular_resumo_da_simulacao(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t)
{
    int quantidade_passos = 0;
    double delta_t_efetivo = 0.0;
    const double valor_inicial_no_tempo = calcular_solucao_exata(valor_inicial_em_zero, modelo_catalogado.coeficiente_lambda, tempo_inicial);

    calcular_solucao_pelo_metodo_theta(
        valor_inicial_no_tempo,
        modelo_catalogado.coeficiente_lambda,
        tempo_inicial,
        tempo_final,
        delta_t,
        0.5,
        quantidade_passos,
        delta_t_efetivo
    );

    return {
        tempo_inicial,
        tempo_final,
        delta_t_efetivo,
        quantidade_passos,
        valor_inicial_em_zero,
        valor_inicial_no_tempo,
        calcular_solucao_exata(valor_inicial_em_zero, modelo_catalogado.coeficiente_lambda, tempo_final)
    };
}

std::optional<QString> validar_parametros_do_modelo(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta)
{
    Q_UNUSED(modelo_catalogado);
    Q_UNUSED(valor_inicial_em_zero);

    if (delta_t <= 0.0) {
        return QString("O incremento de tempo delta t deve ser maior que zero.");
    }

    if (theta < 0.0 || theta > 1.0) {
        return QString("O parametro theta deve permanecer no intervalo [0, 1].");
    }

    if (std::abs(tempo_final - tempo_inicial) < 1e-12) {
        return QString("Os tempos inicial e final devem ser diferentes para comparar os metodos.");
    }

    return std::nullopt;
}

std::vector<TrajetoriaMetodo> calcular_trajetorias(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta_usuario)
{
    const double valor_inicial_no_tempo = calcular_solucao_exata(valor_inicial_em_zero, modelo_catalogado.coeficiente_lambda, tempo_inicial);

    return {
        calcular_trajetoria_pelo_metodo_theta("Explicito", QColor(255, 107, 107), valor_inicial_no_tempo, modelo_catalogado.coeficiente_lambda, tempo_inicial, tempo_final, delta_t, 0.0),
        calcular_trajetoria_pelo_metodo_theta("Semi-implicito", QColor(255, 193, 77), valor_inicial_no_tempo, modelo_catalogado.coeficiente_lambda, tempo_inicial, tempo_final, delta_t, 0.5),
        calcular_trajetoria_pelo_metodo_theta("Implicito", QColor(114, 197, 255), valor_inicial_no_tempo, modelo_catalogado.coeficiente_lambda, tempo_inicial, tempo_final, delta_t, 1.0),
        calcular_trajetoria_pelo_metodo_theta(QString("Theta = %1").arg(theta_usuario, 0, 'g', 4), QColor(186, 139, 255), valor_inicial_no_tempo, modelo_catalogado.coeficiente_lambda, tempo_inicial, tempo_final, delta_t, theta_usuario)
    };
}
