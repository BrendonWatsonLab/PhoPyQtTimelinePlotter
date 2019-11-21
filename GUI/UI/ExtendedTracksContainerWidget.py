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

    def __init__(self, duration, length, *args, **kwargs):
        super(ExtendedTracksContainerWidget, self).__init__(duration, length, *args, **kwargs)

        self.backgroundColor = ExtendedTracksContainerWidget.defaultBackgroundColor

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, self.length, 200)
        
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

        
    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        self.draw_indicator_lines(qp)

        # Clear clip path
        path = QPainterPath()
        path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        qp.setClipPath(path)

        qp.end()



    def sizeHint(self):
        return QSize(20, 120)

    # Mouse movement
    def mouseMoveEvent(self, e):
        self.pos = e.pos()
        x = self.pos.x()
        self.hoverChanged.emit(x)
        self.update()



