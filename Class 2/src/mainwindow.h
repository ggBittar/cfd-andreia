#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class FunctionSelector;
class GraphWidget;

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private:
    FunctionSelector *functionSelector_;
    GraphWidget *graphWidget_;
    Ui::MainWindow *ui;
};

#endif // MAINWINDOW_H
