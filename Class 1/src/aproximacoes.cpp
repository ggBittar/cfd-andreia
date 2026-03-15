#include "aproximacoes.hpp"

#include <algorithm>
#include <cmath>

namespace {
constexpr int quantidade_maxima_iteracoes = 40;
constexpr double tolerancia_iteracao = 1e-10;

double calcular_erro_absoluto(double valor_aproximado, double valor_exato)
{
    return std::abs(valor_aproximado - valor_exato);
}

double limitar_theta(double theta)
{
    return std::clamp(theta, 0.0, 1.0);
}
}

double avancar_metodo_theta(
    const std::function<double(double, double)>& lado_direito,
    double tempo_atual,
    double valor_atual,
    double delta_t,
    double theta
)
{
    const double theta_limitado = limitar_theta(theta);
    const double tempo_seguinte = tempo_atual + delta_t;
    const double contribuicao_explicita = valor_atual + delta_t * (1.0 - theta_limitado) * lado_direito(tempo_atual, valor_atual);

    if (theta_limitado <= 1e-12) {
        return contribuicao_explicita;
    }

    double valor_iterado = contribuicao_explicita;
    for (int iteracao = 0; iteracao < quantidade_maxima_iteracoes; ++iteracao) {
        const double proximo_valor = contribuicao_explicita + delta_t * theta_limitado * lado_direito(tempo_seguinte, valor_iterado);
        if (std::abs(proximo_valor - valor_iterado) < tolerancia_iteracao) {
            return proximo_valor;
        }
        valor_iterado = proximo_valor;
    }

    return valor_iterado;
}

double calcular_solucao_pelo_metodo_theta(
    const std::function<double(double, double)>& lado_direito,
    double valor_inicial,
    double tempo_inicial,
    double tempo_final,
    double delta_t,
    double theta,
    int& quantidade_passos,
    double& delta_t_efetivo
)
{
    const double intervalo_total = tempo_final - tempo_inicial;
    double tempo_atual = tempo_inicial;
    double valor_atual = valor_inicial;
    const double direcao = intervalo_total >= 0.0 ? 1.0 : -1.0;
    const double delta_t_assinado = direcao * delta_t;
    const double duracao_total = std::abs(intervalo_total);
    const int quantidade_passos_completos = static_cast<int>(std::floor(duracao_total / delta_t));
    const double duracao_restante = duracao_total - (static_cast<double>(quantidade_passos_completos) * delta_t);

    quantidade_passos = quantidade_passos_completos;
    for (int passo = 0; passo < quantidade_passos_completos; ++passo) {
        valor_atual = avancar_metodo_theta(lado_direito, tempo_atual, valor_atual, delta_t_assinado, theta);
        tempo_atual += delta_t_assinado;
    }

    if (duracao_restante > 1e-12) {
        const double ultimo_passo = direcao * duracao_restante;
        valor_atual = avancar_metodo_theta(lado_direito, tempo_atual, valor_atual, ultimo_passo, theta);
        ++quantidade_passos;
    }

    if (quantidade_passos == 0) {
        valor_atual = avancar_metodo_theta(lado_direito, tempo_atual, valor_atual, intervalo_total, theta);
        quantidade_passos = 1;
        delta_t_efetivo = intervalo_total;
        return valor_atual;
    }

    delta_t_efetivo = quantidade_passos_completos > 0 ? delta_t_assinado : intervalo_total;
    return valor_atual;
}

TrajetoriaMetodo calcular_trajetoria_pelo_metodo_theta(
    const QString& nome_metodo,
    const QColor& cor,
    const std::function<double(double, double)>& lado_direito,
    double valor_inicial,
    double tempo_inicial,
    double tempo_final,
    double delta_t,
    double theta
)
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
        valor_atual = avancar_metodo_theta(lado_direito, tempo_atual, valor_atual, delta_t_assinado, theta);
        tempo_atual += delta_t_assinado;
        trajetoria.pontos.push_back({tempo_atual, valor_atual});
    }

    if (duracao_restante > 1e-12) {
        const double ultimo_passo = direcao * duracao_restante;
        valor_atual = avancar_metodo_theta(lado_direito, tempo_atual, valor_atual, ultimo_passo, theta);
        tempo_atual += ultimo_passo;
        trajetoria.pontos.push_back({tempo_atual, valor_atual});
    } else if (quantidade_passos_completos == 0) {
        valor_atual = avancar_metodo_theta(lado_direito, tempo_atual, valor_atual, intervalo_total, theta);
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
            "Modelo com solucao exponencial crescente.",
            "u(t) = u(0)e^t",
            "u'(t) = u(t)",
            [](double u_zero, double t) { return u_zero * std::exp(t); },
            [](double u_zero, double t) { return u_zero * std::exp(t); },
            [](double, double u) { return u; }
        },
        {
            "Decaimento Exponencial",
            "Modelo com solucao exponencial decrescente.",
            "u(t) = u(0)e^(-t)",
            "u'(t) = -u(t)",
            [](double u_zero, double t) { return u_zero * std::exp(-t); },
            [](double u_zero, double t) { return -u_zero * std::exp(-t); },
            [](double, double u) { return -u; }
        },
        {
            "Polinomial Cubico",
            "Modelo polinomial para testar estimativas em derivadas nao lineares no tempo.",
            "u(t) = u(0) + t^3 - 2t^2 + t",
            "u'(t) = 3t^2 - 4t + 1",
            [](double u_zero, double t) { return u_zero + (t * t * t) - (2.0 * t * t) + t; },
            [](double, double t) { return (3.0 * t * t) - (4.0 * t) + 1.0; },
            [](double t, double) { return (3.0 * t * t) - (4.0 * t) + 1.0; }
        },
        {
            "Polinomial Quadratico",
            "Modelo polinomial simples para comparacao em malhas mais grossas.",
            "u(t) = u(0) + 0.5t^2 - 3t",
            "u'(t) = t - 3",
            [](double u_zero, double t) { return u_zero + 0.5 * t * t - 3.0 * t; },
            [](double, double t) { return t - 3.0; },
            [](double t, double) { return t - 3.0; }
        }
    };
}

std::vector<ResultadoMetodo> calcular_resultados(const ModeloCatalogado& modelo_catalogado, double valor_inicial_em_zero, double tempo_inicial, double tempo_final, double delta_t, double theta_usuario)
{
    const double valor_inicial_no_tempo = modelo_catalogado.funcao_exata(valor_inicial_em_zero, tempo_inicial);
    const double valor_exato = modelo_catalogado.funcao_exata(valor_inicial_em_zero, tempo_final);

    std::vector<ResultadoMetodo> resultados;
    resultados.reserve(4);

    const auto adicionar_resultado = [&](const QString& nome_metodo, double theta) {
        int quantidade_passos = 0;
        double delta_t_efetivo = 0.0;
        const double valor_aproximado = calcular_solucao_pelo_metodo_theta(
            modelo_catalogado.lado_direito,
            valor_inicial_no_tempo,
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
    const double valor_inicial_no_tempo = modelo_catalogado.funcao_exata(valor_inicial_em_zero, tempo_inicial);

    calcular_solucao_pelo_metodo_theta(
        modelo_catalogado.lado_direito,
        valor_inicial_no_tempo,
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
        modelo_catalogado.funcao_exata(valor_inicial_em_zero, tempo_final)
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
    const double valor_inicial_no_tempo = modelo_catalogado.funcao_exata(valor_inicial_em_zero, tempo_inicial);

    return {
        calcular_trajetoria_pelo_metodo_theta("Explicito", QColor(255, 107, 107), modelo_catalogado.lado_direito, valor_inicial_no_tempo, tempo_inicial, tempo_final, delta_t, 0.0),
        calcular_trajetoria_pelo_metodo_theta("Semi-implicito", QColor(255, 193, 77), modelo_catalogado.lado_direito, valor_inicial_no_tempo, tempo_inicial, tempo_final, delta_t, 0.5),
        calcular_trajetoria_pelo_metodo_theta("Implicito", QColor(114, 197, 255), modelo_catalogado.lado_direito, valor_inicial_no_tempo, tempo_inicial, tempo_final, delta_t, 1.0),
        calcular_trajetoria_pelo_metodo_theta(QString("Theta = %1").arg(theta_usuario, 0, 'g', 4), QColor(186, 139, 255), modelo_catalogado.lado_direito, valor_inicial_no_tempo, tempo_inicial, tempo_final, delta_t, theta_usuario)
    };
}
