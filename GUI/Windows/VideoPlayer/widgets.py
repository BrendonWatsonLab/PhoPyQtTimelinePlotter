#!/usr/bin/env python
# -*- coding: utf-8 -*-

import platform
import os
import sys
from PyQt5.QtWidgets import QFrame, QSlider, QStyle, QStyleOptionSlider, \
    QPlainTextEdit, QPushButton, QMacCocoaViewContainer
from PyQt5.QtGui import QPalette, QColor, QWheelEvent, QKeyEvent, QPainter, \
    QPen
from PyQt5.QtCore import pyqtSignal, QRect

""" VideoFrame: the frame that contains the VLC video player
"""
class VideoFrame(QFrame):
    """
    A frame used specifically for video/media purpose
    """
    clicked = pyqtSignal()
    doubleClicked = pyqtSignal()
    wheel = pyqtSignal(QWheelEvent)
    keyPressed = pyqtSignal(QKeyEvent)

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)

        if platform.system() == "Darwin": # for MacOS
            self.mac_view = QMacCocoaViewContainer(0, parent=self)
        else:
            self.mac_view = None

        self.original_parent = parent
        self.palette = self.palette()
        self.palette.setColor(QPalette.Window, QColor(0,0,0))

        self.setPalette(self.palette)
        self.setAutoFillBackground(True)


    def mouseReleaseEvent(self, _):
        self.clicked.emit()

    def mouseDoubleClickEvent(self, _):
        self.doubleClicked.emit()

    def wheelEvent(self, event):
        self.wheel.emit(event)

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)    

class HighlightedJumpSlider(QSlider):
    """
    Slider that allows user to jump to any point on it, regardless of steps.
    It also supports partial highlighting.
    """
    def __init__(self, parent=None):
        super(HighlightedJumpSlider, self).__init__(parent)
        self.highlightStart = None
        self.highlightEnd = None

    def mousePressEvent(self, ev):
        """ Jump to click position """
        self.setValue(QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), ev.x(), self.width())
        )

    def mouseMoveEvent(self, ev):
        """ Jump to pointer position while moving """
        self.setValue(QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), ev.x(), self.width())
        )

    def setHighlight(self, start, end):
        if start is not None and end is not None and start < end:
            self.highlightStart, self.highlightEnd = start, end

    def paintEvent(self, event):
        if self.highlightStart is not None and self.highlightEnd is not None:
            p = QPainter(self)
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            gr = self.style().subControlRect(QStyle.CC_Slider, opt,
                                             QStyle.SC_SliderGroove, self)
            rectX, rectY, rectW, rectH = gr.getRect()
            startX = int(
                (rectW/(self.maximum() - self.minimum()))
                * self.highlightStart + rectX
            )
            startY = (rectH - rectY) / 2
            width = int(
                (rectW/(self.maximum() - self.minimum()))
                * self.highlightEnd + rectX
            ) - startX
            height = (rectH - startY) / 2
            c = QColor(0, 152, 116)
            p.setBrush(c)
            c.setAlphaF(0.3)
            p.setPen(QPen(c, 1.0))
            rectToPaint = QRect(startX, startY, width, height)
            p.drawRects(rectToPaint)
        super(HighlightedJumpSlider, self).paintEvent(event)


class PlainTextEdit(QPlainTextEdit):
    """
    For some reason Qt refuses to style readOnly QPlainTextEdit correctly, so
    this class is a workaround for that
    """
    def setReadOnly(self, readOnly):
        super(PlainTextEdit, self).setReadOnly(readOnly)
        if readOnly:
            self.setStyleSheet("QPlainTextEdit {"
                               "background-color: #F0F0F0;"
                               "color: #808080;"
                               "border: 1px solid #B0B0B0;"
                               "border-radius: 2px;"
                               "}")
        elif not readOnly:
            self.setStyleSheet("QPlainTextEdit {"
                               "background-color: #FFFFFF;"
                               "color: #000000;"
                               "border: 1px solid #B0B0B0;"
                               "border-radius: 2px;"
                               "}")


class ToggleButton(QPushButton):
    """
    This is a QPushButton that supports toggling. It can have two states: True
    or False, each has its own set of text and icon. The button is controlled
    by a ToggleButtonModel. Without a model, the button behaves exactly like
    a QPushButton
    """
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(ToggleButton, self).__init__(parent)
        self.model = None
        self.clicked.connect(self.toggle)

    def toggle(self):
        if not self.model:
            return
        self.model.setState(not self.model.getState())

    def _stateChangeHandler(self):
        if not self.model:
            return
        self.setText(self.model.getText(self.model.getState()))
        self.setIcon(self.model.getIcon(self.model.getState()))
        self.stateChanged.emit(self.model.getState())

    def setModel(self, model):
        """
        Use a model for this button. The model will notify this button when a
        new state is required
        :param model: The model to use
        :return: None
        """
        self.model = model
        self._stateChangeHandler()
        self.model.dataChanged.connect(self._stateChangeHandler)
        self.model.stateChanged.connect(self._stateChangeHandler)

