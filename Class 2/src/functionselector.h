#ifndef FUNCTIONSELECTOR_H
#define FUNCTIONSELECTOR_H

#include "functioncatalog.h"

#include <QList>
#include <QWidget>

class QComboBox;
class QLineEdit;
class QLabel;

class FunctionSelector : public QWidget {
    Q_OBJECT

public:
    explicit FunctionSelector(QWidget *parent = nullptr);

signals:
    void functionSelected(const NamedFunction &function, double xMin, double xMax, double tf, const QList<int> &nValues);

private slots:
    void emitSelection();

private:
    QComboBox *functionComboBox_;
    QLineEdit *xMinInput_;
    QLineEdit *xMaxInput_;
    QLineEdit *tfInput_;
    QLineEdit *nValuesInput_;
    QLabel *statusLabel_;
};

#endif // FUNCTIONSELECTOR_H
