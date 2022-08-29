import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPainterPath, QPolygon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from enum import Enum


class TriangleDrawOption_Horizontal(Enum):
        LeftApex = 1 # Apex is aligned with the left side
        CenterApex = 2 #  Apex is center aligned
        RightApex = 3  # Apex is aligned with the right side


class TrianglePainter(QObject):
    def __init__(self, apex_align_horizontal=TriangleDrawOption_Horizontal.CenterApex):
        super(TrianglePainter, self).__init__()
        self.apex_align_horizontal = apex_align_horizontal

    def get_poly(self, startPos, triangle_height, triangle_width):
        half_triangle_width = (triangle_width / 2.0)
        nibExtremaXPosition = (startPos+triangle_width)

        if (self.apex_align_horizontal is TriangleDrawOption_Horizontal.LeftApex):
            nibApexXPosition = startPos
        elif (self.apex_align_horizontal is TriangleDrawOption_Horizontal.CenterApex):
            nibApexXPosition = (startPos+half_triangle_width)
        elif (self.apex_align_horizontal is TriangleDrawOption_Horizontal.RightApex):
            nibApexXPosition = (startPos+triangle_width)
        else:
            print('ERROR! Invalid type!')
            return None

        out_poly = QPolygon([QPoint(startPos, triangle_height),
                             QPoint(nibExtremaXPosition, triangle_height),
                             QPoint(nibApexXPosition, 0)])

        return out_poly



        