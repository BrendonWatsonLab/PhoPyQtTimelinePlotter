import sys
from datetime import datetime, timedelta, timezone

import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

## INCLUDES:
# from phopyqttimelineplotter.GUI.Helpers.MouseTrackingThroughChildrenMixin import MouseTrackingThroughChildrenMixin


class MouseTrackingThroughChildrenMixin(object):
    """Overrides the default QWidget.setMouseTracking(...) function to recurrsively set mouse tracking to be enabled on all children."""

    def setMouseTracking(self, flag):
        def recursive_set(parent):
            for child in parent.findChildren(QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)

        QWidget.setMouseTracking(self, flag)
        recursive_set(self)
