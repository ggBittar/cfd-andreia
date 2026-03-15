#include "functionselector.h"

#include <QComboBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QRegularExpression>
#include <QVBoxLayout>

namespace {
QList<int> parseNValues(const QString &text)
{
    QList<int> values;
    const QStringList parts = text.split(QRegularExpression("[,;\\s]+"), Qt::SkipEmptyParts);

    for (const QString &part : parts) {
        bool ok = false;
        const int value = part.toInt(&ok);
        if (ok) {
            values.append(value);
        }
    }

    return values;
}
}

FunctionSelector::FunctionSelector(QWidget *parent)
    : QWidget(parent),
      functionComboBox_(new QComboBox(this)),
      xMinInput_(new QLineEdit(this)),
      xMaxInput_(new QLineEdit(this)),
      tfInput_(new QLineEdit(this)),
      nValuesInput_(new QLineEdit(this)),
      statusLabel_(new QLabel(this))
{
    QVBoxLayout *layout = new QVBoxLayout(this);

    QLabel *titleLabel = new QLabel("Selecione a formulação em função de Phi, o domínio de x, o tempo final tf e os valores de N:", this);
    titleLabel->setWordWrap(true);
    layout->addWidget(titleLabel);

    layout->addWidget(new QLabel("Funcao:", this));
    for (const NamedFunction &function : availableFunctions()) {
        functionComboBox_->addItem(function.label, function.id);
    }
    layout->addWidget(functionComboBox_);

    layout->addWidget(new QLabel("Dominio de x:", this));
    QHBoxLayout *domainLayout = new QHBoxLayout();
    xMinInput_->setPlaceholderText("xmin");
    xMinInput_->setText("-25.1327412");
    xMaxInput_->setPlaceholderText("xmax");
    xMaxInput_->setText("25.1327412");
    domainLayout->addWidget(xMinInput_);
    domainLayout->addWidget(xMaxInput_);
    layout->addLayout(domainLayout);

    layout->addWidget(new QLabel("Tempo final tf:", this));
    tfInput_->setPlaceholderText("Ex.: 2.0");
    tfInput_->setText("25.1327412");
    layout->addWidget(tfInput_);

    layout->addWidget(new QLabel("Vetor de N:", this));
    nValuesInput_->setPlaceholderText("Ex.: 1, 2, 4, 8");
    nValuesInput_->setText("1, 2, 4, 8, 16, 32");
    layout->addWidget(nValuesInput_);

    QLabel *helpLabel = new QLabel(
        "Formulação atual: u(x, t, N) = c - 2 nu Phi_x / Phi. N aceita vírgula, ponto e vírgula ou espaço.",
        this);
    helpLabel->setWordWrap(true);
    layout->addWidget(helpLabel);

    QPushButton *applyButton = new QPushButton("Aplicar e Plotar", this);
    layout->addWidget(applyButton);
    statusLabel_->setWordWrap(true);
    layout->addWidget(statusLabel_);
    layout->addStretch();

    connect(applyButton, &QPushButton::clicked, this, &FunctionSelector::emitSelection);
    connect(functionComboBox_, &QComboBox::currentIndexChanged, this, [this](int) { emitSelection(); });
    connect(xMinInput_, &QLineEdit::returnPressed, this, &FunctionSelector::emitSelection);
    connect(xMaxInput_, &QLineEdit::returnPressed, this, &FunctionSelector::emitSelection);
    connect(tfInput_, &QLineEdit::returnPressed, this, &FunctionSelector::emitSelection);
    connect(nValuesInput_, &QLineEdit::returnPressed, this, &FunctionSelector::emitSelection);

    statusLabel_->setStyleSheet("color: #5c677d;");
    statusLabel_->setText("Defina os parametros e clique em Aplicar e Plotar.");
}

void FunctionSelector::emitSelection()
{
    bool minOk = false;
    bool maxOk = false;
    bool tfOk = false;
    const double xMin = xMinInput_->text().toDouble(&minOk);
    const double xMax = xMaxInput_->text().toDouble(&maxOk);
    const double tf = tfInput_->text().toDouble(&tfOk);
    const QList<int> nValues = parseNValues(nValuesInput_->text());

    if (!minOk || !maxOk) {
        statusLabel_->setStyleSheet("color: #a61e4d;");
        statusLabel_->setText("Informe xmin e xmax com numeros validos.");
        return;
    }

    if (xMin >= xMax) {
        statusLabel_->setStyleSheet("color: #a61e4d;");
        statusLabel_->setText("O dominio deve satisfazer xmin < xmax.");
        return;
    }

    if (!tfOk || tf < 0.0) {
        statusLabel_->setStyleSheet("color: #a61e4d;");
        statusLabel_->setText("Informe um tempo final tf valido.");
        return;
    }

    if (nValues.isEmpty()) {
        statusLabel_->setStyleSheet("color: #a61e4d;");
        statusLabel_->setText("Informe pelo menos um valor inteiro para N.");
        return;
    }

    const NamedFunction function = findFunctionById(functionComboBox_->currentData().toString());
    if (!function.evaluator) {
        statusLabel_->setStyleSheet("color: #a61e4d;");
        statusLabel_->setText("Selecione uma funcao valida.");
        return;
    }

    statusLabel_->setStyleSheet("color: #2b8a3e;");
    statusLabel_->setText(
        QString("Aplicado: x em [%1, %2], tf = %3, N = {%4}.")
            .arg(xMin, 0, 'g', 6)
            .arg(xMax, 0, 'g', 6)
            .arg(tf, 0, 'g', 6)
            .arg(nValuesInput_->text().trimmed()));

    emit functionSelected(function, xMin, xMax, tf, nValues);
}
