#ifndef LATEXWIDGET_H
#define LATEXWIDGET_H

#include <QWidget>

#if defined(CLASS2_HAS_WEBENGINE)
class QWebEngineView;
#else
class QTextBrowser;
#endif

class LatexWidget : public QWidget {
    Q_OBJECT

public:
    explicit LatexWidget(QWidget *parent = nullptr);

private:
#if defined(CLASS2_HAS_WEBENGINE)
    QWebEngineView *viewer_;
#else
    QTextBrowser *viewer_;
#endif
};

#endif // LATEXWIDGET_H
