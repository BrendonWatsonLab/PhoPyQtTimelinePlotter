#!/usr/bin/python3
# -*- coding: utf-8 -*-
# FixedTimelineContentsWidthMixin.py
# from datetime import datetime, timezone, timedelta

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (
    QLine,
    QMargins,
    QObject,
    QPoint,
    QRect,
    QRectF,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
    QPolygon,
)
from PyQt5.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

## IMPORT:
# from phopyqttimelineplotter.GUI.Helpers.FixedTimelineContentsWidthMixin import FixedTimelineContentsWidthMixin


class FixedTimelineContentsWidthMixin(object):
    """
    # Requires:
        Requires self.fixedWidth be set in initializer
    """

    @pyqtSlot(float)
    def set_fixed_width(self, newWidth):
        """Called on the width changing"""
        self.fixedWidth = newWidth
        # self.resize(self.fixedWidth, self.height())
        self.setMinimumWidth(self.fixedWidth)
        self.update()

    def minimumSizeHint(self) -> QSize:
        return QSize(self.fixedWidth, 50)

    def sizeHint(self) -> QSize:
        return QSize(self.fixedWidth, 100)
