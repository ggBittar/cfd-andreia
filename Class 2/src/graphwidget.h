#ifndef GRAPHWIDGET_H
#define GRAPHWIDGET_H

#include "functioncatalog.h"

#include <QColor>
#include <QList>
#include <QMouseEvent>
#include <QPointF>
#include <QVector>
#include <QWheelEvent>
#include <QWidget>

class QPaintEvent;
class QResizeEvent;
class QLabel;
class QSlider;

class GraphWidget : public QWidget {
    Q_OBJECT

public:
    explicit GraphWidget(QWidget *parent = nullptr);

public slots:
    void setPlotDefinition(const NamedFunction &function, double xMin, double xMax, double tf, const QList<int> &nValues);

protected:
    void paintEvent(QPaintEvent *event) override;
    void resizeEvent(QResizeEvent *event) override;
    void wheelEvent(QWheelEvent *event) override;
    void mouseDoubleClickEvent(QMouseEvent *event) override;

private:
    void recomputeCurves();
    void updateTimeLabel();
    double currentTime() const;
    QRectF plotArea() const;
    QPointF mapToScreen(const QPointF &point, const QRectF &area, double xMin, double xMax, double yMin, double yMax) const;
    double mapToModelX(double xScreen, const QRectF &area, double xMin, double xMax) const;
    void resetZoom();

    struct CurveData {
        int n = 0;
        QVector<QPointF> samples;
        QColor color;
    };

    QVector<CurveData> curves_;
    QList<int> nValues_;
    NamedFunction selectedFunction_;
    QString errorMessage_;
    double xMin_ = 0.0;
    double xMax_ = 1.0;
    double tf_ = 0.0;
    bool customZoom_ = false;
    double visibleXMin_ = 0.0;
    double visibleXMax_ = 1.0;
    double visibleYMin_ = -1.0;
    double visibleYMax_ = 1.0;
    QLabel *timeLabel_;
    QSlider *timeSlider_;
};

#endif // GRAPHWIDGET_H
