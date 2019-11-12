# EventsDrawingWindow.py
# Draws the main window containing several EventTrackDrawingWidgets

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir


from GUI.HelpWindow.HelpWindowFinal import *

# from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget import *
from GUI.UI.qtimeline import *

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Events import *
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Partition import *
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_AnnotationComments import *

from app.database.SqliteEventsDatabase import load_video_events_from_database
from app.database.SqlAlchemyDatabase import load_annotation_events_from_database, save_annotation_events_to_database, create_TimestampedAnnotation

from GUI.UI.VideoPlayer.main_video_player_window import *
from GUI.SetupWindow.SetupWindow import *

class GlobalTimeAdjustmentOptions(Enum):
        ConstrainGlobalToVideoTimeRange = 1 # adjusts the global start and end times for the timeline to the range of the loaded videos.
        ConstrainVideosShownToGlobal = 2 #  keeps the global the same, and only shows the videos within the global start and end range
        ConstantOffsetFromMostRecentVideo = 3  # adjusts the global to a fixed time prior to the end of the most recent video.


class TimelineDrawingWindow(QtWidgets.QMainWindow):
    
    static_VideoTrackTrackID = -1 # The integer ID of the main video track
    
    TraceCursorWidth = 2
    TraceCursorColor = QColor(51, 255, 102)  # Green

    GlobalTimelineConstraintOptions = GlobalTimeAdjustmentOptions.ConstantOffsetFromMostRecentVideo
    # ConstrainToVideoTimeRange = True # If true, adjusts the global start and end times for the timeline to the range of the loaded videos.
    # # If false, only shows the videos within the global start and end range

    # Only used if GlobalTimelineConstraintOptions is .ConstantOffsetFromMostRecentVideo. Specifies the offset prior to the end of the last video which to start the global timeline.
    ConstantOffsetFromMostRecentVideoDuration = timedelta(days=7)

    def __init__(self, totalStartTime, totalEndTime):
        super(TimelineDrawingWindow, self).__init__() # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/MainWindow/MainWindow.ui", self) # Load the .ui file
        
        self.scaleMultiplier = 4.0
        self.update_global_start_end_times(totalStartTime, totalEndTime)

        self.videoInfoObjects = load_video_events_from_database(as_videoInfo_objects=True)
        self.build_video_display_events()

        self.videoPlayerWindow = None
        self.helpWindow = None
        self.setupWindow = None

        self.initUI()
        # self.show() # Show the GUI


    def initUI(self):

        """ View Hierarchy:
            self.verticalSplitter
                self.videoPlayerContainer
                self.timelineScroll: QScrollArea
                    .widget = self.extendedTracksContainer
                        extendedTracksContainer -> extendedTracksContainerVboxLayout
                        self.timelineMasterTrackWidget
                        self.mainVideoTrack
                        () All in self.eventTrackWidgets:
                            self.annotationCommentsTrackWidget
                            self.partitionsTrackWidget
                            self.partitionsTwoTrackWidget
        """

        # Nested helper function to initialize the menu bar
        def initUI_initMenuBar(self):
            # action_exit = QAction(QIcon('exit.png'), '&Exit', self)        
            # action_exit.setShortcut('Ctrl+Q')
            # action_exit.setStatusTip('Exit application')
            # action_exit.triggered.connect(qApp.quit)

            self.ui.actionExit_Application.triggered.connect(qApp.quit)
            self.ui.actionShow_Help.triggered.connect(self.handle_showHelpWindow)
            self.ui.actionVideo_Player.triggered.connect(self.handle_showVideoPlayerWindow)
            self.ui.actionSettings.triggered.connect(self.handle_showSetupWindow)
            

        desiredWindowWidth = 900
        self.resize( desiredWindowWidth, 800 )

        # Setup the menubar
        initUI_initMenuBar(self)

        # minimumWidgetWidth = 500
        minimumWidgetWidth = self.width() * self.scaleMultiplier

        # Video Player Container: the container that holds the video player
        self.videoPlayerContainer = QtWidgets.QWidget()
        ## TODO: Add the video player to the container.
        ## TODO: Needs a layout
        
        ## Define WIDGETS:

        ## Timeline Tracks:

        # Timeline Numberline track:
        masterTimelineDurationSeconds = self.totalDuration.total_seconds()
        self.timelineMasterTrackWidget = QTimeLine(masterTimelineDurationSeconds, minimumWidgetWidth)


        # Video Track
        ## TODO: The video tracks must set:
        self.mainVideoTrack = TimelineTrackDrawingWidget_Events(-1, self.videoEventDisplayObjects, [], self.totalStartTime, self.totalEndTime)
        self.mainVideoTrack.selection_changed.connect(self.handle_child_selection_event)
        self.mainVideoTrack.hover_changed.connect(self.handle_child_hover_event)
        self.mainVideoTrack.setMouseTracking(True)
        self.mainVideoTrack.shouldDismissSelectionUponMouseButtonRelease = False
        self.mainVideoTrack.itemSelectionMode = ItemSelectionOptions.SingleSelection

        # Other Tracks:
        self.eventTrackWidgets = []

        # Annotation Comments track:
        self.annotationCommentsTrackWidget = TimelineTrackDrawingWidget_AnnotationComments(0, [], [], self.totalStartTime, self.totalEndTime)
        self.eventTrackWidgets.append(self.annotationCommentsTrackWidget)

        # Partition tracks:
        self.partitionsTrackWidget = TimelineTrackDrawingWidget_Partition(1, None, [], self.totalStartTime, self.totalEndTime)
        self.eventTrackWidgets.append(self.partitionsTrackWidget)

        self.partitionsTwoTrackWidget = TimelineTrackDrawingWidget_Partition(2, None, [], self.totalStartTime, self.totalEndTime)
        self.eventTrackWidgets.append(self.partitionsTwoTrackWidget)

        # Build the bottomPanelWidget
        self.extendedTracksContainer = QtWidgets.QWidget()
        self.extendedTracksContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.extendedTracksContainer.setAutoFillBackground(True)
        self.extendedTracksContainer.setMouseTracking(True)

        # Debug Pallete
        # p = self.labjackEventsContainer.palette()
        # p.setColor(self.labjackEventsContainer.backgroundRole(), Qt.red)
        # self.labjackEventsContainer.setPalette(p)

        #Layout of Extended Tracks Container Widget
        self.extendedTracksContainerVboxLayout = QVBoxLayout(self)
        self.extendedTracksContainerVboxLayout.addStretch(1)
        self.extendedTracksContainerVboxLayout.addSpacing(2.0)
        self.extendedTracksContainerVboxLayout.setContentsMargins(0,0,0,0)

        self.extendedTracksContainerVboxLayout.addWidget(self.timelineMasterTrackWidget)
        self.timelineMasterTrackWidget.setMinimumSize(minimumWidgetWidth, 50)
        self.timelineMasterTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.extendedTracksContainerVboxLayout.addWidget(self.mainVideoTrack)
        self.mainVideoTrack.setMinimumSize(minimumWidgetWidth, 50)
        self.mainVideoTrack.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)


        #Layout of Main Window:

        # Loop through the eventTrackWidgets and add them
        for i in range(0, len(self.eventTrackWidgets)):
            currWidget = self.eventTrackWidgets[i]
            self.extendedTracksContainerVboxLayout.addWidget(currWidget)
            currWidget.setMinimumSize(minimumWidgetWidth,50)
            currWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.extendedTracksContainer.setLayout(self.extendedTracksContainerVboxLayout)

        self.extendedTracksContainer.setFixedWidth(minimumWidgetWidth)
        ## Scroll Area: should contain only the extendedTracksContainer (not the video container)
        self.timelineScroll = QScrollArea()
        self.timelineScroll.setWidget(self.extendedTracksContainer)
        self.timelineScroll.setWidgetResizable(True)
        self.timelineScroll.setMouseTracking(True)
        # self.timelineScroll.setFixedHeight(400)
        # self.timelineScroll.setFixedWidth(self.width())

        # Main Vertical Splitter:
        self.verticalSplitter = QSplitter(Qt.Vertical)
        self.verticalSplitter.setHandleWidth(8)
        self.verticalSplitter.setMouseTracking(True)
        self.verticalSplitter.addWidget(self.videoPlayerContainer)
        self.verticalSplitter.addWidget(self.timelineScroll)

        # Size the widgets
        self.verticalSplitter.setSizes([100, 600])

        # Complete setup
        self.setCentralWidget( self.verticalSplitter )
        self.setMouseTracking(True)
        self.statusBar()

        self.setWindowTitle('Pho Timeline Test Drawing Window')

        # Cursor tracking
        self.cursorX = 0.0
        self.cursorY = 0.0
        #self.cursorTraceRect = QRect(0,0,0,0)


    def update_global_start_end_times(self, totalStartTime, totalEndTime):
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)

    # Build the PhoDurationEvent objects that are displayed in the main video timeline to represent the videos
    def build_video_display_events(self):
        videoDates = []
        videoEndDates = []
        # self.videoLabels = []
        self.videoEventDisplayObjects = []
        for videoInfoItem in self.videoInfoObjects:
            if (videoInfoItem.is_original_video):
                videoDates.append(videoInfoItem.startTime)
                videoEndDates.append(videoInfoItem.endTime)
                currExtraInfoDict = videoInfoItem.get_output_dict()
                # Event Generation
                currEvent = PhoDurationEvent(videoInfoItem.startTime, videoInfoItem.endTime, videoInfoItem.fullName, QColor(51,204,255), currExtraInfoDict)
                self.videoEventDisplayObjects.append(currEvent)

        self.videoDates = np.array(videoDates)
        self.videoEndDates = np.array(videoEndDates)
        
        self.earliestVideoTime = self.videoDates.min()
        self.latestVideoTime = self.videoEndDates.max()
        print('earliest video: ', self.earliestVideoTime)
        print('latest video: ', self.latestVideoTime)


        if TimelineDrawingWindow.GlobalTimelineConstraintOptions is GlobalTimeAdjustmentOptions.ConstrainGlobalToVideoTimeRange:
            # adjusts the global start and end times for the timeline to the range of the loaded videos.
            self.update_global_start_end_times(self.earliestVideoTime, self.latestVideoTime)
        elif TimelineDrawingWindow.GlobalTimelineConstraintOptions is GlobalTimeAdjustmentOptions.ConstrainVideosShownToGlobal:
            # Otherwise filter the videos
            ## TODO: Filter the videoEvents, self.videoDates, self.videoEndDates, and labels if we need them to the global self.totalStartTime and self.totalEndTime range
            pass
        elif TimelineDrawingWindow.GlobalTimelineConstraintOptions is GlobalTimeAdjustmentOptions.ConstantOffsetFromMostRecentVideo:
            # Otherwise filter the videos
            newLatestTime = self.latestVideoTime
            newEarliestTime = newLatestTime - TimelineDrawingWindow.ConstantOffsetFromMostRecentVideoDuration
            self.update_global_start_end_times(newEarliestTime, newLatestTime)

            ## TODO: Filter the videoEvents, self.videoDates, self.videoEndDates, and labels if we need them to the global self.totalStartTime and self.totalEndTime range
            # Set an "isInViewport" option or something
        else:
            print('INVALID ENUM VALUE!!!')

        

    # Timeline position/time converion functions:
    def offset_to_percent(self, event_x, event_y):
        percent_x = event_x / (self.width() * self.scaleMultiplier)
        percent_y = event_y / self.height()
        return (percent_x, percent_y)

    def offset_to_duration(self, event_x):
        (percent_x, percent_y) = self.offset_to_percent(event_x, 0.0)
        return (self.totalDuration * percent_x)

    def offset_to_datetime(self, event_x):
        duration_offset = self.offset_to_duration(event_x)
        return (self.totalStartTime + duration_offset)

    # Event Handlers:
    def keyPressEvent(self, event):
        # TODO: pass to all children
        self.mainVideoTrack.keyPressEvent(event)

        
        # self.partitionsTrackWidget.keyPressEvent(event)

    def mouseMoveEvent(self, event):
        self.cursorX = event.x()
        self.cursorY = event.y()
        duration_offset = self.offset_to_duration(self.cursorX)
        datetime = self.offset_to_datetime(self.cursorX)
        text = "window x: {0},  duration: {1}, datetime: {2}".format(self.cursorX, duration_offset, datetime)
        # Call the on_mouse_moved handler for the video track which will update its .hovered_object property, which is then read and used for relative offsets
        # self.partitionsTrackWidget.on_mouse_moved(event)
        self.mainVideoTrack.on_mouse_moved(event)
        # TODO: Need to use offset into scroll view instead of window?
        potentially_hovered_child_object = self.mainVideoTrack.hovered_object
        if potentially_hovered_child_object:
            relative_duration_offset = potentially_hovered_child_object.compute_relative_offset_duration(datetime)
            text = text + ' -- relative to duration: {0}'.format(relative_duration_offset)

        self.statusBar().showMessage(text)


    # Shows the help/instructions window:
    def handle_showHelpWindow(self):
        if self.helpWindow:
            self.helpWindow.show()
        else:
            # Create a new help window
            self.helpWindow = HelpWindowFinal()
            self.helpWindow.show()

    # Shows the Setup/Settings window:
    def handle_showSetupWindow(self):
        if self.setupWindow:
            self.setupWindow.show()
        else:
            # Create a new setup window
            self.setupWindow = SetupWindow()
            self.setupWindow.show()

    # Shows the video player window:
    def handle_showVideoPlayerWindow(self):
        if self.videoPlayerWindow:
            self.videoPlayerWindow.show()
        else:
            # Create a new videoPlayerWindow window
            self.videoPlayerWindow = MainVideoPlayerWindow()
            self.videoPlayerWindow.show()

    def try_set_video_player_window_url(self, url):
        if self.videoPlayerWindow:
            print("Using existing Video Player Window...")
            self.videoPlayerWindow.set_timestamp_filename(r"C:\Users\halechr\repo\looper\testdata\NewTimestamps.tmsp")
            self.videoPlayerWindow.set_video_filename(url)
            # self.videoPlayerWindow.show()
        else:
            # Create a new videoPlayerWindow window
            print("Creating new Video Player Window...")
            self.videoPlayerWindow = MainVideoPlayerWindow()
            self.videoPlayerWindow.set_timestamp_filename(r"C:\Users\halechr\repo\looper\testdata\NewTimestamps.tmsp")
            self.videoPlayerWindow.set_video_filename(url)
            # self.videoPlayerWindow.show()

        
        

    # @pyqtSlot(int, int)
    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_selection_event(self, trackIndex, trackObjectIndex):
        text = "handle_child_selection_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
        print(text)
        if trackIndex == TimelineDrawingWindow.static_VideoTrackTrackID:
            # If it's the video track
            if trackObjectIndex == TimelineTrackDrawingWidget_Events.static_TimeTrackObjectIndex_NoSelection:
                # No selection, just clear the filters
                for i in range(0, len(self.eventTrackWidgets)):
                    currWidget = self.eventTrackWidgets[i]
                    currWidget.set_active_filter(self.totalStartTime, self.totalEndTime)
            else:
                # Get the selected video object
                # currHoveredObject = self.mainVideoTrack.hovered_object

                # currSelectedObjectIndex = self.mainVideoTrack.selected_duration_object_indicies[0]
                currSelectedObjectIndex = trackObjectIndex
                currSelectedObject = self.mainVideoTrack.durationObjects[trackObjectIndex]
                
                if currSelectedObject:
                    selected_video_path = currSelectedObject.extended_data['path']
                    print(selected_video_path)
                    self.try_set_video_player_window_url(str(selected_video_path))
                # Iterate through the timeline tracks to filter based on the video.
                # for i in range(0, len(self.eventTrackWidgets)):
                #     currWidget = self.eventTrackWidgets[i]
                #     currWidget.set_active_filter(currHoveredObject.startTime, currHoveredObject.endTime)


    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_hover_event(self, trackIndex, trackObjectIndex):
        text = "handle_child_hover_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
        # print(text)

    def refresh_child_widget_display(self):
        for i in range(0, len(self.eventTrackWidgets)):
            currWidget = self.eventTrackWidgets[i]
            currWidget.update()

