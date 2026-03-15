#include "graphwidget.h"

#include <QLabel>
#include <QPaintEvent>
#include <QPainter>
#include <QPainterPath>
#include <QPen>
#include <QResizeEvent>
#include <QSignalBlocker>
#include <QSlider>
#include <QtGlobal>
#include <algorithm>
#include <cmath>

namespace {
constexpr int leftMargin = 52;
constexpr int rightMargin = 20;
constexpr int topMargin = 20;
constexpr int bottomMargin = 56;
constexpr int gridLines = 8;

QColor colorForIndex(int index)
{
    static const QVector<QColor> palette = {
        QColor(84, 191, 160),
        QColor(235, 125, 89),
        QColor(106, 160, 255),
        QColor(232, 193, 112),
        QColor(192, 132, 252),
        QColor(123, 203, 111)
    };
    return palette.at(index % palette.size());
}
}

GraphWidget::GraphWidget(QWidget *parent)
    : QWidget(parent),
      timeLabel_(new QLabel(this)),
      timeSlider_(new QSlider(Qt::Horizontal, this))
{
    setMinimumSize(420, 320);
    setAutoFillBackground(true);

    timeSlider_->setRange(0, 200);
    timeSlider_->setValue(0);
    timeLabel_->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    updateTimeLabel();

    connect(timeSlider_, &QSlider::valueChanged, this, [this]() {
        updateTimeLabel();
        recomputeCurves();
    });
}

void GraphWidget::setPlotDefinition(const NamedFunction &function, double xMin, double xMax, double tf, const QList<int> &nValues)
{
    selectedFunction_ = function;
    xMin_ = xMin;
    xMax_ = xMax;
    tf_ = tf;

    timeSlider_->setEnabled(tf_ > 0.0);
    {
        const QSignalBlocker blocker(timeSlider_);
        timeSlider_->setValue(0);
    }
    updateTimeLabel();

    curves_.clear();
    errorMessage_.clear();

    if (!selectedFunction_.evaluator) {
        errorMessage_ = "Selecione uma funcao valida.";
        update();
        return;
    }

    nValues_.clear();
    nValues_ = nValues;
    customZoom_ = false;
    recomputeCurves();
}

void GraphWidget::resizeEvent(QResizeEvent *event)
{
    QWidget::resizeEvent(event);

    const int margin = 16;
    const int sliderHeight = 24;
    const int labelWidth = 120;
    const int bottomY = height() - margin - sliderHeight;

    timeSlider_->setGeometry(margin, bottomY, width() - (3 * margin) - labelWidth, sliderHeight);
    timeLabel_->setGeometry(width() - margin - labelWidth, bottomY, labelWidth, sliderHeight);
}

void GraphWidget::recomputeCurves()
{
    curves_.clear();
    errorMessage_.clear();

    if (!selectedFunction_.evaluator) {
        update();
        return;
    }

    constexpr int sampleCount = 400;
    const double t = currentTime();

    for (int index = 0; index < nValues_.size(); ++index) {
        const int n = nValues_.at(index);
        CurveData curve;
        curve.n = n;
        curve.color = colorForIndex(index);
        curve.samples.reserve(sampleCount);

        for (int sample = 0; sample < sampleCount; ++sample) {
            const double ratio = sampleCount > 1 ? static_cast<double>(sample) / (sampleCount - 1) : 0.0;
            const double x = xMin_ + (xMax_ - xMin_) * ratio;

            const double y = selectedFunction_.evaluator(x, t, n);
            if (!std::isfinite(y)) {
                continue;
            }

            curve.samples.append(QPointF(x, y));
        }

        if (!curve.samples.isEmpty()) {
            curves_.append(curve);
        }
    }

    if (curves_.isEmpty()) {
        errorMessage_ = "Nenhum ponto valido foi gerado para o grafico.";
    }

    resetZoom();

    update();
}

void GraphWidget::updateTimeLabel()
{
    timeLabel_->setText(QString("t = %1 / %2").arg(currentTime(), 0, 'f', 3).arg(tf_, 0, 'f', 3));
}

double GraphWidget::currentTime() const
{
    if (tf_ <= 0.0) {
        return 0.0;
    }

    return tf_ * static_cast<double>(timeSlider_->value()) / static_cast<double>(timeSlider_->maximum());
}

QRectF GraphWidget::plotArea() const
{
    return QRectF(
        leftMargin,
        topMargin,
        std::max(120, width() - leftMargin - rightMargin),
        std::max(120, height() - topMargin - bottomMargin)
    );
}

QPointF GraphWidget::mapToScreen(const QPointF &point, const QRectF &area, double xMin, double xMax, double yMin, double yMax) const
{
    const double xRatio = (point.x() - xMin) / (xMax - xMin);
    const double yRatio = (point.y() - yMin) / (yMax - yMin);

    return QPointF(
        area.left() + xRatio * area.width(),
        area.bottom() - yRatio * area.height()
    );
}

double GraphWidget::mapToModelX(double xScreen, const QRectF &area, double xMin, double xMax) const
{
    const double ratio = (xScreen - area.left()) / area.width();
    return xMin + ratio * (xMax - xMin);
}

void GraphWidget::resetZoom()
{
    visibleXMin_ = xMin_;
    visibleXMax_ = xMax_;

    if (curves_.isEmpty()) {
        visibleYMin_ = -1.0;
        visibleYMax_ = 1.0;
        customZoom_ = false;
        return;
    }

    double yMin = curves_.first().samples.first().y();
    double yMax = yMin;

    for (const CurveData &curve : curves_) {
        for (const QPointF &point : curve.samples) {
            yMin = std::min(yMin, point.y());
            yMax = std::max(yMax, point.y());
        }
    }

    if (std::abs(yMax - yMin) < 1e-9) {
        yMin -= 1.0;
        yMax += 1.0;
    } else {
        const double margin = (yMax - yMin) * 0.15;
        yMin -= margin;
        yMax += margin;
    }

    visibleYMin_ = yMin;
    visibleYMax_ = yMax;
    customZoom_ = false;
}

void GraphWidget::wheelEvent(QWheelEvent *event)
{
    if (curves_.isEmpty() || !errorMessage_.isEmpty()) {
        event->ignore();
        return;
    }

    const QRectF area = plotArea();
    if (!area.contains(event->position())) {
        event->ignore();
        return;
    }

    const double xMin = visibleXMin_;
    const double xMax = visibleXMax_;
    const double yMin = visibleYMin_;
    const double yMax = visibleYMax_;
    const double factor = event->angleDelta().y() > 0 ? 0.85 : 1.15;
    const double centerX = mapToModelX(event->position().x(), area, xMin, xMax);
    const double centerY = yMax - ((event->position().y() - area.top()) / area.height()) * (yMax - yMin);
    const double newWidth = std::max(0.001, (xMax - xMin) * factor);
    const double newHeight = std::max(0.001, (yMax - yMin) * factor);
    const double ratioX = (centerX - xMin) / (xMax - xMin);
    const double ratioY = (centerY - yMin) / (yMax - yMin);

    visibleXMin_ = centerX - ratioX * newWidth;
    visibleXMax_ = visibleXMin_ + newWidth;
    visibleYMin_ = centerY - ratioY * newHeight;
    visibleYMax_ = visibleYMin_ + newHeight;
    customZoom_ = true;

    update();
    event->accept();
}

void GraphWidget::mouseDoubleClickEvent(QMouseEvent *event)
{
    if (event->button() == Qt::LeftButton) {
        resetZoom();
        update();
        event->accept();
        return;
    }

    QWidget::mouseDoubleClickEvent(event);
}

void GraphWidget::paintEvent(QPaintEvent *event)
{
    QWidget::paintEvent(event);

    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing, true);
    painter.fillRect(rect(), QColor(20, 24, 31));

    const QRectF plotRect = plotArea();
    painter.setPen(QColor(58, 66, 84));
    painter.drawRoundedRect(plotRect.adjusted(-1, -1, 1, 1), 10, 10);

    if (!errorMessage_.isEmpty()) {
        painter.setPen(QColor(226, 149, 120));
        painter.drawText(plotRect, Qt::AlignCenter | Qt::TextWordWrap, errorMessage_);
        return;
    }

    if (curves_.isEmpty()) {
        painter.setPen(QColor(160, 171, 190));
        painter.drawText(plotRect, Qt::AlignCenter, "Aguardando parametros para plotagem.");
        return;
    }

    const double xMin = visibleXMin_;
    const double xMax = visibleXMax_;
    const double yMin = visibleYMin_;
    const double yMax = visibleYMax_;

    QPen gridPen(QColor(44, 50, 63));
    gridPen.setWidth(1);
    painter.setPen(gridPen);

    for (int index = 0; index <= gridLines; ++index) {
        const double ratio = static_cast<double>(index) / gridLines;
        const double x = plotRect.left() + ratio * plotRect.width();
        const double y = plotRect.top() + ratio * plotRect.height();

        painter.drawLine(QPointF(x, plotRect.top()), QPointF(x, plotRect.bottom()));
        painter.drawLine(QPointF(plotRect.left(), y), QPointF(plotRect.right(), y));

        const double xValue = xMin + ratio * (xMax - xMin);
        const double yValue = yMax - ratio * (yMax - yMin);

        painter.setPen(QColor(130, 141, 160));
        painter.drawText(QRectF(x - 28, plotRect.bottom() + 6, 56, 16), Qt::AlignCenter, QString::number(xValue, 'g', 4));
        painter.drawText(QRectF(4, y - 8, leftMargin - 10, 16), Qt::AlignRight | Qt::AlignVCenter, QString::number(yValue, 'g', 4));
        painter.setPen(gridPen);
    }

    QPen axisPen(QColor(115, 132, 158));
    axisPen.setWidth(2);
    painter.setPen(axisPen);

    if (xMin <= 0.0 && xMax >= 0.0) {
        painter.drawLine(
            mapToScreen(QPointF(0.0, yMax), plotRect, xMin, xMax, yMin, yMax),
            mapToScreen(QPointF(0.0, yMin), plotRect, xMin, xMax, yMin, yMax)
        );
    }

    if (yMin <= 0.0 && yMax >= 0.0) {
        painter.drawLine(
            mapToScreen(QPointF(xMin, 0.0), plotRect, xMin, xMax, yMin, yMax),
            mapToScreen(QPointF(xMax, 0.0), plotRect, xMin, xMax, yMin, yMax)
        );
    }

    for (const CurveData &curve : curves_) {
        QPainterPath path;
        bool firstPoint = true;

        for (const QPointF &sample : curve.samples) {
            if (sample.x() < xMin || sample.x() > xMax) {
                firstPoint = true;
                continue;
            }
            const QPointF mappedPoint = mapToScreen(sample, plotRect, xMin, xMax, yMin, yMax);
            if (firstPoint) {
                path.moveTo(mappedPoint);
                firstPoint = false;
            } else {
                path.lineTo(mappedPoint);
            }
        }

        const bool isPrimaryCurve = !nValues_.isEmpty() && curve.n == nValues_.front();
        painter.setPen(QPen(curve.color, isPrimaryCurve ? 3.0 : 2.0));
        painter.drawPath(path);
    }

    const QRectF legendBox(plotRect.right() - 150, plotRect.top() + 10, 140, 28 + curves_.size() * 22);
    painter.setPen(QColor(58, 66, 84));
    painter.setBrush(QColor(16, 20, 26, 210));
    painter.drawRoundedRect(legendBox, 8, 8);

    int legendY = static_cast<int>(legendBox.top()) + 14;
    for (const CurveData &curve : curves_) {
        painter.setPen(QPen(curve.color, 2));
        painter.drawLine(QPointF(legendBox.left() + 10, legendY), QPointF(legendBox.left() + 28, legendY));
        painter.setPen(QColor(230, 235, 242));
        painter.drawText(QRectF(legendBox.left() + 34, legendY - 9, legendBox.width() - 40, 18), Qt::AlignLeft | Qt::AlignVCenter, QString("N = %1").arg(curve.n));
        legendY += 22;
    }

    painter.setPen(QColor(214, 220, 230));
    painter.drawText(QRectF(plotRect.left(), 0, plotRect.width(), 18), Qt::AlignCenter,
                     QString("u(x,t,N) via Phi   |   t = %1").arg(currentTime(), 0, 'f', 3));
}
