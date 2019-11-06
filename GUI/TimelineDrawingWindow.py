# EventsDrawingWindow.py
# Draws the main window containing several EventTrackDrawingWidgets

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

# from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget import *
from GUI.qtimeline import *
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Partition import *


class TimelineDrawingWindow(QtWidgets.QMainWindow):
    TraceCursorWidth = 2
    TraceCursorColor = QColor(51, 255, 102)  # Green

    def __init__(self, totalStartTime, totalEndTime):
        super(TimelineDrawingWindow, self).__init__()

        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime

        self.initUI()


    def initUI(self):

        """
        rootContainer
            videoPlayerContainer
            mainTimelineContainer
                timelineMasterTrackWidget
                extendedTracksContainer
                partitionsTrackWidget
        """


        desiredWindowWidth = 900
        self.resize( desiredWindowWidth, 800 )

        # self.rootContainer = QtWidgets.QWidget()
        
        # Video Player Container: the container that holds the video player
        self.videoPlayerContainer = QtWidgets.QWidget()
        ## TODO: Add the video player to the container.
        ## TODO: Needs a layout
        
        # mainTimelineContainer: the main container that holds the timelineMasterTrack (the numbers and ticks, as well as the playhead up top) in addition to the tracks
        # self.mainTimelineContainer = QtWidgets.QWidget()

        #Layout of Main Window
        # self.mainVBoxLayout = QVBoxLayout(self)
        # self.mainVBoxLayout.addStretch(1)
        # self.mainVBoxLayout.addSpacing(2.0)

        # self.mainVBoxLayout.addWidget(self.videoPlayerContainer)
        # self.videoPlayerContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.videoPlayerContainer.setAutoFillBackground(True)

        # self.mainVBoxLayout.addWidget(self.mainTimelineContainer)
        # self.mainTimelineContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.mainTimelineContainer.setAutoFillBackground(True)

        # self.rootContainer.setLayout(self.mainVBoxLayout)


        ## Timeline Tracks:

        # Timeline Numberline track:
        self.timelineMasterTrackWidget = QTimeLine(360, desiredWindowWidth)

        # Video Tracks
        self.partitionsTrackWidget = TimelineTrackDrawingWidget_Partition(-1, None, [], self.totalStartTime, self.totalEndTime)
        self.partitionsTrackWidget.selection_changed.connect(self.handle_child_selection_event)
        self.partitionsTrackWidget.hover_changed.connect(self.handle_child_hover_event)

        # Labjack Tracks:
        self.eventTrackWidgets = []

        # Build the bottomPanelWidget
        self.extendedTracksContainer = QtWidgets.QWidget()
        self.extendedTracksContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.extendedTracksContainer.setAutoFillBackground(True)
        # Debug Pallete
        # p = self.labjackEventsContainer.palette()
        # p.setColor(self.labjackEventsContainer.backgroundRole(), Qt.red)
        # self.labjackEventsContainer.setPalette(p)

        #Layout of Extended Tracks Container Widget
        self.extendedTracksContainerVboxLayout = QVBoxLayout(self)
        self.extendedTracksContainerVboxLayout.addStretch(1)
        self.extendedTracksContainerVboxLayout.addSpacing(2.0)

        self.extendedTracksContainerVboxLayout.addWidget(self.timelineMasterTrackWidget)
        self.timelineMasterTrackWidget.setMinimumSize(500,50)
        self.timelineMasterTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.extendedTracksContainerVboxLayout.addWidget(self.partitionsTrackWidget)
        self.partitionsTrackWidget.setMinimumSize(500,50)
        self.partitionsTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        for i in range(0, len(self.eventTrackWidgets)):
            currWidget = self.eventTrackWidgets[i]
            self.extendedTracksContainerVboxLayout.addWidget(currWidget)
            currWidget.setMinimumSize(500,50)
            currWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            currWidget.mousePressEvent = currWidget.on_button_clicked
            currWidget.mouseReleaseEvent = currWidget.on_button_released

        self.extendedTracksContainer.setLayout(self.extendedTracksContainerVboxLayout)


        #Layout of Main Timeline Container:
        # self.mainTimelineTracksContainerVboxLayout = QVBoxLayout(self)
        # self.mainTimelineTracksContainerVboxLayout.addStretch(1)
        # self.mainTimelineTracksContainerVboxLayout.addSpacing(2.0)

        # self.mainTimelineTracksContainerVboxLayout.addWidget(self.partitionsTrackWidget)
        # self.partitionsTrackWidget.setMinimumSize(500,50)
        # self.partitionsTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)


        # self.mainTimelineContainer.setLayout(mainTimelineTracksContainerVboxLayout)


        self.verticalSplitter = QSplitter(Qt.Vertical)
        self.verticalSplitter.setHandleWidth(8)
        self.verticalSplitter.setMouseTracking(True)
        self.verticalSplitter.addWidget(self.videoPlayerContainer)
        self.verticalSplitter.addWidget(self.extendedTracksContainer)

        # Size the widgets
        self.verticalSplitter.setSizes([100, 600])

        self.partitionsTrackWidget.mousePressEvent = self.partitionsTrackWidget.on_button_clicked
        self.partitionsTrackWidget.mouseReleaseEvent = self.partitionsTrackWidget.on_button_released

        # Complete setup
        self.setCentralWidget( self.verticalSplitter )
        self.setMouseTracking(True)
        self.statusBar()

        self.setWindowTitle('Pho Timeline Test Drawing Window')

        # Cursor tracking
        self.cursorX = 0.0
        self.cursorY = 0.0
        #self.cursorTraceRect = QRect(0,0,0,0)



    def offset_to_percent(self, event_x, event_y):
        percent_x = event_x / self.width()
        percent_y = event_y / self.height()
        return (percent_x, percent_y)

    def offset_to_duration(self, event_x):
        (percent_x, percent_y) = self.offset_to_percent(event_x, 0.0)
        return (self.partitionsTrackWidget.totalDuration * percent_x)

    def offset_to_datetime(self, event_x):
        duration_offset = self.offset_to_duration(event_x)
        return (self.partitionsTrackWidget.totalStartTime + duration_offset)

    def keyPressEvent(self, event):
        self.partitionsTrackWidget.keyPressEvent(event)

    def mouseMoveEvent(self, event):
        self.cursorX = event.x()
        self.cursorY = event.y()
        duration_offset = self.offset_to_duration(self.cursorX)
        datetime = self.offset_to_datetime(self.cursorX)
        text = "window x: {0},  duration: {1}, datetime: {2}".format(self.cursorX, duration_offset, datetime)
        self.partitionsTrackWidget.on_mouse_moved(event)
        potentially_hovered_child_object = self.partitionsTrackWidget.hovered_object
        if potentially_hovered_child_object:
            relative_duration_offset = potentially_hovered_child_object.compute_relative_offset_duration(datetime)
            text = text + ' -- relative to duration: {0}'.format(relative_duration_offset)

        self.statusBar().showMessage(text)

    # @pyqtSlot(int, int)
    # Occurs when the user selects an object in the video track with the mouse
    def handle_child_selection_event(self, trackIndex, trackObjectIndex):
        text = "handle_child_selection_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
        # print(text)
        if trackIndex == -1:
            # If it's the video track
            if trackObjectIndex == -1:
                # No selection, just clear the filters
                for i in range(0, len(self.eventTrackWidgets)):
                    currWidget = self.eventTrackWidgets[i]
                    currWidget.set_active_filter(self.totalStartTime, self.totalEndTime)
            else:
                # Get the selected video object
                currHoveredObject = self.partitionsTrackWidget.hovered_object
                for i in range(0, len(self.eventTrackWidgets)):
                    currWidget = self.eventTrackWidgets[i]
                    currWidget.set_active_filter(currHoveredObject.startTime, currHoveredObject.endTime)


    # Occurs when the user selects an object in the video track with the mouse
    def handle_child_hover_event(self, trackIndex, trackObjectIndex):
        text = "handle_child_hover_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
        # print(text)

    def refresh_child_widget_display(self):
        for i in range(0, len(self.eventTrackWidgets)):
            currWidget = self.eventTrackWidgets[i]
            currWidget.update()

