#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import tempfile
from base64 import b64encode
from datetime import datetime, timedelta, timezone

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

__backgroudColor__ = QColor(60, 63, 65)

from phopyqttimelineplotter.GUI.Helpers.DateTimeRenders import DateTimeRenderMixin
from phopyqttimelineplotter.GUI.Helpers.FixedTimelineContentsWidthMixin import (
    FixedTimelineContentsWidthMixin,
)
from phopyqttimelineplotter.GUI.Model.ReferenceLines.ReferenceLineManager import (
    ReferenceMarkerManager,
)
from phopyqttimelineplotter.GUI.Model.ReferenceLines.ReferenceMarkerVisualHelpers import (
    ReferenceMarker,
    TickProperties,
)


class TickedTimelineDrawingBaseWidget(
    DateTimeRenderMixin, FixedTimelineContentsWidthMixin, QWidget
):
    """A class that draws "ticks" which are evenly spaced lines along its entire width.
    Used by qtimeline.py and ExtendedTrackContainerWidget.py
    """

    hoverChanged = pyqtSignal(int)
    positionChanged = pyqtSignal(int)

    defaultActiveColor = Qt.darkCyan
    defaultNowColor = Qt.red

    # static lines
    staticTimeDelininationTickLineProperties = TickProperties(
        QColor(187, 187, 187), 2.6, Qt.SolidLine
    )
    staticTimeDelininationMinorTickLineProperties = TickProperties(
        QColor(187, 187, 187), 0.6, Qt.SolidLine
    )

    # dynamic (moving) lines
    videoPlaybackLineProperties = TickProperties(Qt.red, 1.0, Qt.SolidLine)
    hoverLineProperties = TickProperties(Qt.cyan, 0.8, Qt.DashLine)

    def __init__(
        self, totalStartTime, totalEndTime, totalDuration, duration, parent=None
    ):
        super(TickedTimelineDrawingBaseWidget, self).__init__(parent=parent)
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = totalDuration

        self.duration = duration

        # Reference Manager:
        self.referenceManager = parent.get_reference_manager()

        # Set variables
        self.fixedWidth = 800.0
        self.backgroundColor = __backgroudColor__
        self.pos = None
        self.video_pos = None
        self.pointerPos = None
        self.clicking = False  # Check if mouse left button is being pressed
        self.is_in = False  # check if user is in the widget
        self.activeColor = TickedTimelineDrawingBaseWidget.defaultActiveColor
        self.nowColor = TickedTimelineDrawingBaseWidget.defaultNowColor

        self.is_driven_externally = False

        self.setMouseTracking(True)  # Mouse events
        self.setAutoFillBackground(True)  # background

        # set background
        pal = QPalette()
        pal.setColor(QPalette.Background, self.backgroundColor)
        self.setPalette(pal)

    def get_reference_manager(self):
        return self.referenceManager

    def draw_tick_lines(self, painter):
        # Draw dash lines
        # point = 0
        painter.setPen(
            TickedTimelineDrawingBaseWidget.staticTimeDelininationTickLineProperties.get_pen()
        )
        # draw a horizontal line (Currently draws the line a fixed distance in pixels apart. The labels are only added in qtimeline)
        painter.drawLine(0, 40, self.width(), 40)

        # Major markers (day markers)
        for aStaticMarkerData in self.referenceManager.get_static_major_marker_data():
            item_x_offset = self.referenceManager.compute_x_offset_from_datetime(
                self.width(), aStaticMarkerData.time
            )
            painter.drawLine(item_x_offset, 40, item_x_offset, 20)

        painter.setPen(
            TickedTimelineDrawingBaseWidget.staticTimeDelininationMinorTickLineProperties.get_pen()
        )

        # Minor Markers
        for aStaticMarkerData in self.referenceManager.get_static_minor_marker_data():
            item_x_offset = self.referenceManager.compute_x_offset_from_datetime(
                self.width(), aStaticMarkerData.time
            )
            painter.drawLine(item_x_offset, 40, item_x_offset, 30)

    # Draws the tick marks and the indicator lines
    def draw_indicator_lines(self, painter):

        # Draw video playback indicator line
        # videoPlaybackIndicatorMarkerContainer = self.referenceManager.get_indicator_marker_video_playback()
        # # Update hover line visibility
        # hoverIndicatorMarkerContainer = self.referenceManager.get_indicator_marker_user_hover()
        # hoverIndicatorMarkerContainer.get_view().updateIsEnabled((self.is_in or self.is_driven_externally))

        # Draw video playback indicator line
        if self.video_pos is not None:
            painter.setPen(
                TickedTimelineDrawingBaseWidget.videoPlaybackLineProperties.get_pen()
            )
            painter.drawLine(self.video_pos.x(), 0, self.video_pos.x(), self.height())

        # Draw hover line
        if self.pos is not None:
            if self.is_in or self.is_driven_externally:
                painter.setPen(
                    TickedTimelineDrawingBaseWidget.hoverLineProperties.get_pen()
                )
                painter.drawLine(self.pos.x(), 0, self.pos.x(), self.height())

        pass

    def paintRect(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        self.draw_tick_lines(qp)
        self.draw_indicator_lines(qp)

        self.get_reference_manager().draw(qp, event.rect(), self.getScale())

        # # Clear clip path
        # path = QPainterPath()
        # path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        # qp.setClipPath(path)

        qp.end()

    # Mouse movement
    def mouseMoveEvent(self, e):
        QWidget.mouseMoveEvent(self, e)
        pass

    #  (NEVER CALLED)
    def mouseMoveRect(self, e):
        self.pos = e.pos()
        x = self.pos.x()

        self.hoverChanged.emit(x)

        # if mouse is being pressed, update pointer
        if self.clicking:
            self.pointerPos = x
            self.positionChanged.emit(x)
            self.pointerTimePos = self.pointerPos * self.getScale()

        self.update()

    # Mouse pressed (NEVER CALLED)
    def mousePressRect(self, e):
        if e.button() == Qt.LeftButton:
            x = e.pos().x()
            self.pointerPos = x
            self.positionChanged.emit(x)
            self.pointerTimePos = self.pointerPos * self.getScale()

            self.update()
            self.clicking = True  # Set clicking check to true

    # Mouse release
    def mouseReleaseRect(self, e):
        if e.button() == Qt.LeftButton:
            self.clicking = False  # Set clicking check to false

    # Enter (NEVER CALLED)
    def enterRect(self, e):
        self.is_in = True
        self.is_driven_externally = False

    # Leave (NEVER CALLED)
    def leaveRect(self, e):
        self.is_in = False
        self.update()

    # Get scale from length
    def getScale(self):
        return float(self.duration) / float(self.width())

    # Get duration
    def getDuration(self):
        return self.duration

    # Set background color
    def setBackgroundColor(self, color):
        self.backgroundColor = color

    @pyqtSlot(float)
    def on_update_reference_marker_position(self, pointer_desired_x):
        self.get_reference_manager().update_next_unused_marker(pointer_desired_x)
        self.update()

    @pyqtSlot(float)
    def on_update_selected_position(self, pointer_desired_x):
        self.pointerPos = pointer_desired_x
        self.positionChanged.emit(pointer_desired_x)
        self.pointerTimePos = self.pointerPos * self.getScale()
        self.update()

    @pyqtSlot(int)
    def on_update_hover(self, x):
        self.is_driven_externally = True
        self.pos = QPoint(x, 0)
        self.update()

    @pyqtSlot(int)
    def on_update_video_line(self, x):
        # passing in None for x allows the line to be removed
        if x is None:
            self.video_pos = None
        else:
            self.video_pos = QPoint(x, 0)

        self.update()

    # Main Window Slots:
    @pyqtSlot()
    def on_active_zoom_changed(self):
        # print("TickedTimelineDrawingBaseWidget.on_active_zoom_changed(...)")
        self.update()

    @pyqtSlot()
    def on_active_viewport_changed(self):
        # print("TickedTimelineDrawingBaseWidget.on_active_viewport_changed(...)")
        self.update()

    @pyqtSlot(datetime, datetime, timedelta)
    def on_active_global_timeline_times_changed(
        self, totalStartTime, totalEndTime, totalDuration
    ):
        # print("TickedTimelineDrawingBaseWidget.on_active_global_timeline_times_changed({0}, {1}, {2})".format(str(totalStartTime), str(totalEndTime), str(totalDuration)))
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = totalDuration
        self.update()
        return
