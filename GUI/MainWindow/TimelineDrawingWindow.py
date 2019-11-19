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


from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWindow

from GUI.HelpWindow.HelpWindowFinal import *

# from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget import *
from GUI.UI.qtimeline import *

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Events import *
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Partition import *
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_AnnotationComments import *

# from app.database.SqliteEventsDatabase import load_video_events_from_database
from app.database.SqlAlchemyDatabase import load_annotation_events_from_database, save_annotation_events_to_database, create_TimestampedAnnotation

from GUI.UI.VideoPlayer.main_video_player_window import *
from GUI.SetupWindow.SetupWindow import *

class GlobalTimeAdjustmentOptions(Enum):
        ConstrainGlobalToVideoTimeRange = 1 # adjusts the global start and end times for the timeline to the range of the loaded videos.
        ConstrainVideosShownToGlobal = 2 #  keeps the global the same, and only shows the videos within the global start and end range
        ConstantOffsetFromMostRecentVideo = 3  # adjusts the global to a fixed time prior to the end of the most recent video.


class TimelineDrawingWindow(AbstractDatabaseAccessingWindow):
    
    static_VideoTrackTrackID = -1 # The integer ID of the main video track
    
    TraceCursorWidth = 2
    TraceCursorColor = QColor(51, 255, 102)  # Green

    GlobalTimelineConstraintOptions = GlobalTimeAdjustmentOptions.ConstrainGlobalToVideoTimeRange
    # GlobalTimelineConstraintOptions = GlobalTimeAdjustmentOptions.ConstantOffsetFromMostRecentVideo

    # ConstrainToVideoTimeRange = True # If true, adjusts the global start and end times for the timeline to the range of the loaded videos.
    # # If false, only shows the videos within the global start and end range

    # Only used if GlobalTimelineConstraintOptions is .ConstantOffsetFromMostRecentVideo. Specifies the offset prior to the end of the last video which to start the global timeline.
    ConstantOffsetFromMostRecentVideoDuration = timedelta(days=7)

    # DefaultZoom = 4.0
    DefaultZoom = 16.0
    ZoomDelta = 1.0
    MinZoomLevel = 0.1
    MaxZoomLevel = 2600.0
    

    def __init__(self, database_connection, totalStartTime, totalEndTime):
        super(TimelineDrawingWindow, self).__init__(database_connection) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/MainWindow/MainWindow.ui", self) # Load the .ui file

        self.activeScaleMultiplier = TimelineDrawingWindow.DefaultZoom
        self.update_global_start_end_times(totalStartTime, totalEndTime)

        # self.videoInfoObjects = load_video_events_from_database(self.database_connection.get_path(), as_videoInfo_objects=True)
        self.videoInfoObjects = []
        self.reloadModelFromDatabase()

        self.build_video_display_events()

        self.videoPlayerWindow = None
        self.helpWindow = None
        self.setupWindow = None

        self.setMouseTracking(True)
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
            
            ## Setup Zoom:
            self.ui.actionZoom_In.triggered.connect(self.on_zoom_in)
            self.ui.actionZoom_Default.triggered.connect(self.on_zoom_home)
            self.ui.actionZoom_Out.triggered.connect(self.on_zoom_out)


        desiredWindowWidth = 900
        self.resize( desiredWindowWidth, 800 )

        # Setup the menubar
        initUI_initMenuBar(self)

        # minimumWidgetWidth = 500
        minimumWidgetWidth = self.get_minimum_track_width()

        # Toolbar
        # self.ui.dockWidget_FooterToolbar
        self.ui.doubleSpinBox_currentZoom.setValue(self.activeScaleMultiplier)

        # Video Player Container: the container that holds the video player
        self.videoPlayerContainer = QtWidgets.QWidget()
        self.videoPlayerContainer.setMouseTracking(True)
        ## TODO: Add the video player to the container.
        ## TODO: Needs a layout
        
        ## Define WIDGETS:

        ## Timeline Tracks:

        # Timeline Numberline track:
        masterTimelineDurationSeconds = self.totalDuration.total_seconds()
        self.timelineMasterTrackWidget = QTimeLine(masterTimelineDurationSeconds, minimumWidgetWidth)
        self.timelineMasterTrackWidget.setMouseTracking(True)

        # Video Tracks
        ## TODO: The video tracks must set:
        self.videoFileTrackWidgets = []

        # self.allVideoEventDisplayObjects.filter()
        self.mainVideoTrack = TimelineTrackDrawingWidget_Events(-1, self.trackVideoEventDisplayObjects[0], [], self.totalStartTime, self.totalEndTime, self.database_connection)
        self.videoFileTrackWidgets.append(self.mainVideoTrack)

        self.labeledVideoTrack = TimelineTrackDrawingWidget_Events(-1, self.trackVideoEventDisplayObjects[1], [], self.totalStartTime, self.totalEndTime, self.database_connection)
        self.videoFileTrackWidgets.append(self.labeledVideoTrack)


        # Other Tracks:
        self.eventTrackWidgets = []

        # Annotation Comments track:
        self.annotationCommentsTrackWidget = TimelineTrackDrawingWidget_AnnotationComments(0, [], [], self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
        self.eventTrackWidgets.append(self.annotationCommentsTrackWidget)

        # Partition tracks:
        self.partitionsTrackWidget = TimelineTrackDrawingWidget_Partition(1, None, [], self.totalStartTime, self.totalEndTime, self.database_connection)
        self.eventTrackWidgets.append(self.partitionsTrackWidget)

        self.partitionsTwoTrackWidget = TimelineTrackDrawingWidget_Partition(2, None, [], self.totalStartTime, self.totalEndTime, self.database_connection)
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


        # self.extendedTracksContainerVboxLayout.addWidget(self.mainVideoTrack)
        # self.mainVideoTrack.setMinimumSize(minimumWidgetWidth, 50)
        # self.mainVideoTrack.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)


        #Layout of Main Window:

       # Loop through the videoFileTrackWidgets and add them
        for i in range(0, len(self.videoFileTrackWidgets)):
            currVideoTrackWidget = self.videoFileTrackWidgets[i]
            # Video track specific setup
            currVideoTrackWidget.selection_changed.connect(self.handle_child_selection_event)
            currVideoTrackWidget.hover_changed.connect(self.handle_child_hover_event)
            currVideoTrackWidget.setMouseTracking(True)
            currVideoTrackWidget.shouldDismissSelectionUponMouseButtonRelease = False
            currVideoTrackWidget.itemSelectionMode = ItemSelectionOptions.SingleSelection
            # General Layout:
            self.extendedTracksContainerVboxLayout.addWidget(currVideoTrackWidget)
            currVideoTrackWidget.setMinimumSize(minimumWidgetWidth,50)
            currVideoTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)


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
        self.verticalSplitter.setMouseTracking(True)

        # Size the widgets
        self.verticalSplitter.setSizes([100, 600])

        # Complete setup
        self.setCentralWidget( self.verticalSplitter )
        self.setMouseTracking(True)
        self.statusBar()

        self.setWindowTitle('Pho Timeline Test Drawing Window')

        # Toolbar
        self.ui.lblActiveViewportDuration.setText(str(self.get_active_viewport_duration()))
        self.ui.lblActiveTotalTimelineDuration.setText(str(self.totalDuration))

        # Cursor tracking
        self.cursorX = 0.0
        self.cursorY = 0.0
        #self.cursorTraceRect = QRect(0,0,0,0)

            
    def reloadModelFromDatabase(self):
        self.videoFileRecords = self.database_connection.load_video_file_info_from_database()
        # Iterate through loaded database records to build videoInfoObjects
        for aVideoFileRecord in self.videoFileRecords:
            aVideoInfoObj = aVideoFileRecord.get_video_info_obj()
            self.videoInfoObjects.append(aVideoInfoObj)

    def update_global_start_end_times(self, totalStartTime, totalEndTime):
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)

    # Build the PhoDurationEvent objects that are displayed in the main video timeline to represent the videos
    def build_video_display_events(self):
        videoDates = []
        videoEndDates = []
        # self.videoLabels = []
        self.allVideoEventDisplayObjects = []
        self.trackVideoEventDisplayObjects = [[], []]
        for videoInfoItem in self.videoInfoObjects:
            videoDates.append(videoInfoItem.startTime)
            videoEndDates.append(videoInfoItem.endTime)
            currExtraInfoDict = videoInfoItem.get_output_dict()
            # Event Generation
            currEvent = PhoDurationEvent(videoInfoItem.startTime, videoInfoItem.endTime, videoInfoItem.fullName, QColor(51,204,255), currExtraInfoDict)
            self.allVideoEventDisplayObjects.append(currEvent)
            if videoInfoItem.is_original_video:
                self.trackVideoEventDisplayObjects[0].append(currEvent)
            else:
                self.trackVideoEventDisplayObjects[1].append(currEvent)


        # for videoInfoItem in self.videoInfoObjects:
        #     if (videoInfoItem.is_original_video):
        #         videoDates.append(videoInfoItem.startTime)
        #         videoEndDates.append(videoInfoItem.endTime)
        #         currExtraInfoDict = videoInfoItem.get_output_dict()
        #         # Event Generation
        #         currEvent = PhoDurationEvent(videoInfoItem.startTime, videoInfoItem.endTime, videoInfoItem.fullName, QColor(51,204,255), currExtraInfoDict)
        #         self.videoEventDisplayObjects.append(currEvent)

        self.videoDates = np.array(videoDates)
        self.videoEndDates = np.array(videoEndDates)
        self.allVideoEventDisplayObjects = np.array(self.allVideoEventDisplayObjects)

        if videoDates:
            self.earliestVideoTime = self.videoDates.min()
            self.latestVideoTime = self.videoEndDates.max()
            print('earliest video: ', self.earliestVideoTime)
            print('latest video: ', self.latestVideoTime)
        else:
            print("No videos loaded! Setting self.latestVideoTime to now")
            self.latestVideoTime = datetime.now()
            self.earliestVideoTime = self.latestVideoTime - TimelineDrawingWindow.ConstantOffsetFromMostRecentVideoDuration


        if TimelineDrawingWindow.GlobalTimelineConstraintOptions is GlobalTimeAdjustmentOptions.ConstrainGlobalToVideoTimeRange:
            # adjusts the global start and end times for the timeline to the range of the loaded videos.
            self.update_global_start_end_times(self.earliestVideoTime, self.latestVideoTime)
        elif TimelineDrawingWindow.GlobalTimelineConstraintOptions is GlobalTimeAdjustmentOptions.ConstrainVideosShownToGlobal:
            # Otherwise filter the videos
            ## TODO: Filter the videoEvents, self.videoDates, self.videoEndDates, and labels if we need them to the global self.totalStartTime and self.totalEndTime range
            print("UNIMPLEMENTED TIME ADJUST MODE!!")
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
        percent_x = event_x / (self.width() * self.activeScaleMultiplier)
        percent_y = event_y / self.height()
        return (percent_x, percent_y)

    def offset_to_duration(self, event_x):
        (percent_x, percent_y) = self.offset_to_percent(event_x, 0.0)
        return (self.totalDuration * percent_x)

    def offset_to_datetime(self, event_x):
        duration_offset = self.offset_to_duration(event_x)
        return (self.totalStartTime + duration_offset)

    # Returns the index of the child object that the (x, y) point falls within, or None if it doesn't fall within an event.
    def find_hovered_timeline_track(self, event_x, event_y):
        hovered_timeline_track_object = None
        for (anIndex, aTimelineTrack) in enumerate(self.eventTrackWidgets):
            # aTrackFrame = aTimelineTrack.frameGeometry()
            # aTrackFrame = aTimelineTrack.rect()
            # aTrackFrame = aTimelineTrack.geometry()
            aTrackFrame = aTimelineTrack.frameGeometry()
            
            # print("timeline_track: ", aTrackFrame)
            if aTrackFrame.contains(event_x, event_y):
                hovered_timeline_track_object = aTimelineTrack
                print('active_timeline_track[{0}]'.format(anIndex))
                break
        return hovered_timeline_track_object


    # Event Handlers:
    def keyPressEvent(self, event):
        # TODO: pass to all children
        self.mainVideoTrack.on_key_pressed(event)

        # self.curr_hovered_timeline_track = self.find_hovered_timeline_track(event.x(), event.y())
        # If we have a currently hovered timeline track from the mouseMoveEvent, use it
        # if (self.curr_hovered_timeline_track):
        #     if (self.curr_hovered_timeline_track.wantsKeyboardEvents):
        #         self.curr_hovered_timeline_track.on_key_pressed(event)

        # Enable "globally active" timetline tracks that receive keypress events even if they aren't hovered.
        for (anIndex, aTimelineTrack) in enumerate(self.eventTrackWidgets):
            if (aTimelineTrack.wantsKeyboardEvents):
                aTimelineTrack.on_key_pressed(event)
        
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

        # self.curr_hovered_timeline_track = self.find_hovered_timeline_track(event.x(), event.y())
        # if (self.curr_hovered_timeline_track):
        #     if (self.curr_hovered_timeline_track.wantsMouseEvents):
        #         self.curr_hovered_timeline_track.on_mouse_moved(event)
        # else:
        #     print("No hovered timeline track")

        # Exhaustive event forwarding for all track widgets
        for (anIndex, aTimelineTrack) in enumerate(self.eventTrackWidgets):
            if (aTimelineTrack.wantsMouseEvents):
                aTimelineTrack.on_mouse_moved(event)


        self.statusBar().showMessage(text)

    ## Zoom in/default/out events
    def get_minimum_track_width(self):
        return  (self.width() * self.activeScaleMultiplier)

    def get_viewport_width(self):
        return self.timelineScroll.width()

    # Returns the percent of the total duration that the active viewport is currently displaying
    def get_active_percent_viewport_total(self):
        return (float(self.get_viewport_width()) / float(self.get_minimum_track_width()))

    # Returns the duration of the currently displayed viewport
    def get_active_viewport_duration(self):
        currPercent = self.get_active_percent_viewport_total()
        return (currPercent * self.totalDuration)


    def on_zoom_in(self):
        self.activeScaleMultiplier = min(TimelineDrawingWindow.MaxZoomLevel, (self.activeScaleMultiplier + TimelineDrawingWindow.ZoomDelta))
        self.on_active_zoom_changed()

    def on_zoom_home(self):
        self.activeScaleMultiplier = TimelineDrawingWindow.DefaultZoom
        self.on_active_zoom_changed()

    def on_zoom_out(self):
        self.activeScaleMultiplier = max(TimelineDrawingWindow.MinZoomLevel, (self.activeScaleMultiplier - TimelineDrawingWindow.ZoomDelta))
        self.on_active_zoom_changed()

    # Called after self.activeScaleMultiplier is changed to update everything else
    def on_active_zoom_changed(self):
        self.ui.doubleSpinBox_currentZoom.setValue(self.activeScaleMultiplier)
        self.ui.lblActiveTotalTimelineDuration.setText(str(self.totalDuration))
        self.ui.lblActiveViewportDuration.setText(str(self.get_active_viewport_duration()))
        self.resize_children_on_zoom()
        # self.refresh_child_widget_display()

    def resize_children_on_zoom(self):
        newMinWidth = self.get_minimum_track_width()
        self.extendedTracksContainer.setFixedWidth(newMinWidth)
        self.update()



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
            self.setupWindow.set_database_connection(self.database_connection)
            self.setupWindow.show()
        else:
            # Create a new setup window
            self.setupWindow = SetupWindow(self.database_connection)
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

