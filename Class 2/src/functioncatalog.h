#ifndef FUNCTIONCATALOG_H
#define FUNCTIONCATALOG_H

#include <QList>
#include <QString>
#include <functional>

using TimeDependentFunction = std::function<double(double, double, int)>;

struct NamedFunction {
    QString id;
    QString label;
    QString description;
    TimeDependentFunction evaluator;
};

const QList<NamedFunction> &availableFunctions();
NamedFunction findFunctionById(const QString &id);
QString formulationsHtml();
QString formulationsMathJaxHtml();

#endif // FUNCTIONCATALOG_H
