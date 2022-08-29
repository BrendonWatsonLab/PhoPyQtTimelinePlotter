# extendedTracksContainer
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint, pyqtSlot
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout


## Import:
# from GUI.UI.ExtendedTracksContainerWidget import ExtendedTracksContainerWidget
from GUI.UI.TickedTimelineDrawingBaseWidget import TickProperties, TickedTimelineDrawingBaseWidget


class ExtendedTracksContainerWidget(TickedTimelineDrawingBaseWidget):
    """
    Custom Qt Widget to show a current time indicator behind the tracks
    Demonstrating compound and custom-drawn widget.
    """

    hoverChanged = pyqtSignal(int)
    positionChanged = pyqtSignal(int)
    
    defaultBackgroundColor = QColor(60, 63, 65)
    defaultActiveColor = Qt.darkCyan
    defaultNowColor = Qt.red

    # static lines
    # staticTimeDelininationTickLineProperties = TickProperties(QColor(187, 187, 187, 100), 0.4, Qt.SolidLine)
    staticTimeDelininationTickLineProperties = TickProperties(QColor(187, 187, 187, 100), 0.8, Qt.SolidLine)
    staticTimeDelininationMinorTickLineProperties = TickProperties(QColor(187, 187, 187, 80), 0.4, Qt.SolidLine)


    def __init__(self, totalStartTime, totalEndTime, totalDuration, duration, parent=None, *args, **kwargs):
        super(ExtendedTracksContainerWidget, self).__init__(totalStartTime, totalEndTime, totalDuration, duration, parent=parent, *args, **kwargs)

        self.backgroundColor = ExtendedTracksContainerWidget.defaultBackgroundColor


    
    def draw_tick_lines(self, painter):
        ## Overrides parent's implementation for the larger background view
        # y-positions are offset from the top of the frame
        painter.setPen(ExtendedTracksContainerWidget.staticTimeDelininationTickLineProperties.get_pen())

        # Major markers (day markers)
        for aStaticMarkerData in self.referenceManager.get_static_major_marker_data():
            item_x_offset = self.referenceManager.compute_x_offset_from_datetime(self.width(), aStaticMarkerData.time)
            painter.drawLine(item_x_offset, 0, item_x_offset, self.height())

        painter.setPen(ExtendedTracksContainerWidget.staticTimeDelininationMinorTickLineProperties.get_pen())

        # Minor Markers
        for aStaticMarkerData in self.referenceManager.get_static_minor_marker_data():
            item_x_offset = self.referenceManager.compute_x_offset_from_datetime(self.width(), aStaticMarkerData.time)
            painter.drawLine(item_x_offset, 0, item_x_offset, self.height())


    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        self.draw_tick_lines(qp)
        self.draw_indicator_lines(qp)

        self.get_reference_manager().draw(qp, event.rect(), self.getScale())

        # Clear clip path
        path = QPainterPath()
        path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        qp.setClipPath(path)

        # qp.setClipPath(event.exposedRect)

        qp.end()



    def sizeHint(self):
        return QSize(20, 120)

    # Mouse movement
    def mouseMoveEvent(self, e):
        self.pos = e.pos()
        x = self.pos.x()
        self.hoverChanged.emit(x)
        self.update()
        super().mouseMoveEvent(e)
        




