#include "janela_principal.hpp"

#include <QApplication>
#include <QFile>
#include <QIcon>

namespace {
void carregar_folha_de_estilo(QApplication& aplicacao)
{
    QFile arquivo_de_estilo(":/tema_escuro.qss");
    if (arquivo_de_estilo.open(QIODevice::ReadOnly | QIODevice::Text)) {
        aplicacao.setStyleSheet(QString::fromUtf8(arquivo_de_estilo.readAll()));
    }
}
}

int main(int quantidade_argumentos, char* argumentos[])
{
    QApplication aplicacao(quantidade_argumentos, argumentos);
    carregar_folha_de_estilo(aplicacao);
    aplicacao.setWindowIcon(QIcon(":/icone_aplicacao.svg"));

    JanelaPrincipal janela_principal;
    janela_principal.setWindowIcon(QIcon(":/icone_aplicacao.svg"));
    janela_principal.show();

    return aplicacao.exec();
}
