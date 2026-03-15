#include "latexwidget.h"
#include "functioncatalog.h"

#include <QVBoxLayout>

#if defined(CLASS2_HAS_WEBENGINE)
#include <QtWebEngineWidgets/QWebEngineView>
#else
#include <QTextBrowser>
#endif

LatexWidget::LatexWidget(QWidget *parent)
    : QWidget(parent),
#if defined(CLASS2_HAS_WEBENGINE)
      viewer_(new QWebEngineView(this))
#else
      viewer_(new QTextBrowser(this))
#endif
{
    QVBoxLayout *layout = new QVBoxLayout(this);
#if defined(CLASS2_HAS_WEBENGINE)
    viewer_->setHtml(formulationsMathJaxHtml());
#else
    viewer_->setHtml(formulationsHtml());
#endif
    layout->addWidget(viewer_);
}
