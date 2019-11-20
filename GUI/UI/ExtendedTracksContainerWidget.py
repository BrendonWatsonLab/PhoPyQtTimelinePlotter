# extendedTracksContainer
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint, pyqtSlot
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout


## Import:
# from GUI.UI.ExtendedTracksContainerWidget import ExtendedTracksContainerWidget

class ExtendedTracksContainerWidget(QtWidgets.QWidget):
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
        super(ExtendedTracksContainerWidget, self).__init__(*args, **kwargs)

        self.duration = duration
        self.length = length
        self.backgroundColor = ExtendedTracksContainerWidget.defaultBackgroundColor

        self.pos = None
        self.is_in = False  # check if user is in the widget

        self.is_driven_externally = False

        self.activeColor = ExtendedTracksContainerWidget.defaultActiveColor
        self.nowColor = ExtendedTracksContainerWidget.defaultNowColor

        self.setMouseTracking(True)  # Mouse events
        self.setAutoFillBackground(True)  # background

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, self.length, 200)
        
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

        # Set Background
        pal = QPalette()
        pal.setColor(QPalette.Background, self.backgroundColor)
        self.setPalette(pal)

        
    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        if self.pos is not None:
            if (self.is_in or self.is_driven_externally): 
                qp.setPen(QPen(self.nowColor))
                qp.drawLine(self.pos.x(), 0, self.pos.x(), self.height())

        # Clear clip path
        # path = QPainterPath()
        # path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        # qp.setClipPath(path)

        qp.end()



    def sizeHint(self):
        return QSize(20, 120)

    # Mouse movement
    def mouseMoveEvent(self, e):
        self.pos = e.pos()
        x = self.pos.x()
        self.hoverChanged.emit(x)
        self.update()

    # Enter
    def enterEvent(self, e):
        self.is_in = True
        # print("entered main container!")
        self.is_driven_externally = False

    # Leave
    def leaveEvent(self, e):
        self.is_in = False
        self.update()

    @pyqtSlot(int)
    def on_update_hover(self, x):
        self.is_driven_externally = True
        self.pos = QPoint(x, 0)
        self.update()

