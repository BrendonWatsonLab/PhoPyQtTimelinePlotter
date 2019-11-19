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
        print("exiting main container!")

    @pyqtSlot(int)
    def on_update_hover(self, x):
        self.is_driven_externally = True
        self.pos = QPoint(x, 0)
        self.update()

# class EqualizerBar(QtWidgets.QWidget):

#     def __init__(self, bars, steps, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.setSizePolicy(
#             QtWidgets.QSizePolicy.MinimumExpanding,
#             QtWidgets.QSizePolicy.MinimumExpanding
#         )

#         if isinstance(steps, list):
#             # list of colours.
#             self.n_steps = len(steps)
#             self.steps = steps

#         elif isinstance(steps, int):
#             # int number of bars, defaults to red.
#             self.n_steps = steps
#             self.steps = ['red'] * steps

#         else:
#             raise TypeError('steps must be a list or int')

#         # Bar appearance.
#         self.n_bars = bars
#         self._x_solid_percent = 0.8
#         self._y_solid_percent = 0.8
#         self._background_color = QtGui.QColor('black')
#         self._padding = 25  # n-pixel gap around edge.

#         # Bar behaviour
#         self._timer = None
#         self.setDecayFrequencyMs(100)
#         self._decay = 10

#         # Ranges
#         self._vmin = 0
#         self._vmax = 100

#         # Current values are stored in a list.
#         self._values = [0.0] * bars


#     def paintEvent(self, e):
#         painter = QtGui.QPainter(self)

#         brush = QtGui.QBrush()
#         brush.setColor(self._background_color)
#         brush.setStyle(Qt.SolidPattern)
#         rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
#         painter.fillRect(rect, brush)

#         # Define our canvas.
#         d_height = painter.device().height() - (self._padding * 2)
#         d_width = painter.device().width() - (self._padding * 2)

#         # Draw the bars.
#         step_y = d_height / self.n_steps
#         bar_height = step_y * self._y_solid_percent
#         bar_height_space = step_y * (1 - self._x_solid_percent) / 2

#         step_x = d_width / self.n_bars
#         bar_width = step_x * self._x_solid_percent
#         bar_width_space = step_x * (1 - self._y_solid_percent) / 2

#         for b in range(self.n_bars):

#             # Calculate the y-stop position for this bar, from the value in range.
#             pc = (self._values[b] - self._vmin) / (self._vmax - self._vmin)
#             n_steps_to_draw = int(pc * self.n_steps)

#             for n in range(n_steps_to_draw):
#                 brush.setColor(QtGui.QColor(self.steps[n]))
#                 rect = QtCore.QRect(
#                     self._padding + (step_x * b) + bar_width_space,
#                     self._padding + d_height - ((1 + n) * step_y) + bar_height_space,
#                     bar_width,
#                     bar_height
#                 )
#                 painter.fillRect(rect, brush)

#         painter.end()

#     def sizeHint(self):
#         return QtCore.QSize(20, 120)

#     def _trigger_refresh(self):
#         self.update()

#     def setDecay(self, f):
#         self._decay = float(f)

#     def setDecayFrequencyMs(self, ms):
#         if self._timer:
#             self._timer.stop()

#         if ms:
#             self._timer = QtCore.QTimer()
#             self._timer.setInterval(ms)
#             self._timer.timeout.connect(self._decay_beat)
#             self._timer.start()

#     def _decay_beat(self):
#         self._values = [
#             max(0, v - self._decay)
#             for v in self._values
#         ]
#         self.update()  # Redraw new position.

#     def setValues(self, v):
#         self._values = v
#         self.update()

#     def values(self):
#         return self._values

#     def setRange(self, vmin, vmax):
#         assert float(vmin) < float(vmax)
#         self._vmin, self._vmax = float(vmin), float(vmax)

#     def setColor(self, color):
#         self.steps = [color] * self._bar.n_steps
#         self.update()

#     def setColors(self, colors):
#         self.n_steps = len(colors)
#         self.steps = colors
#         self.update()


#     def setBarPadding(self, i):
#         self._padding = int(i)
#         self.update()


#     def setBarSolidPercent(self, f):
#         self._bar_solid_percent = float(f)
#         self.update()


#     def setBackgroundColor(self, color):
#         self._background_color = QtGui.QColor(color)
#         self.update()

