#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "latexwidget.h"
#include "functionselector.h"
#include "graphwidget.h"

#include <QMetaObject>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent),
      functionSelector_(new FunctionSelector(this)),
      graphWidget_(new GraphWidget(this)),
      ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    // Add tabs
    ui->tabWidget->addTab(new LatexWidget(this), "LaTeX Viewer");
    ui->tabWidget->addTab(functionSelector_, "Function Selector");
    ui->tabWidget->addTab(graphWidget_, "Graph Viewer");

    connect(functionSelector_, &FunctionSelector::functionSelected, graphWidget_, &GraphWidget::setPlotDefinition);
    connect(functionSelector_, &FunctionSelector::functionSelected, this, [this]() {
        ui->tabWidget->setCurrentWidget(graphWidget_);
    });

    QMetaObject::invokeMethod(functionSelector_, "emitSelection", Qt::QueuedConnection);
}

MainWindow::~MainWindow() {
    delete ui;
}
