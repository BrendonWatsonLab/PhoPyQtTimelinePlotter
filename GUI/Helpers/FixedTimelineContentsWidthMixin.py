#!/usr/bin/python3
# -*- coding: utf-8 -*-
# FixedTimelineContentsWidthMixin.py
# from datetime import datetime, timezone, timedelta

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal, pyqtSlot, QObject, QMargins, QSize
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout
import sys
import os

## IMPORT:
# from GUI.Helpers.FixedTimelineContentsWidthMixin import FixedTimelineContentsWidthMixin

## Requires
"""
Requires self.fixedWidth be set in initializer
"""
class FixedTimelineContentsWidthMixin(object):
    # Called on the width changing
    @pyqtSlot(float) 
    def set_fixed_width(self, newWidth):
        self.fixedWidth = newWidth
        # self.resize(self.fixedWidth, self.height())
        self.setMinimumWidth(self.fixedWidth)
        self.update()

    def minimumSizeHint(self) -> QSize:
        return QSize(self.fixedWidth, 50)

    def sizeHint(self) -> QSize:
        return QSize(self.fixedWidth, 100)
