# EventsDrawingWindow.py
# Draws the main window containing several EventTrackDrawingWidgets

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QGridLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir


from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWindow

from GUI.HelpWindow.HelpWindowFinal import *
from GUI.MainObjectListsWindow.MainObjectListsWindow import *
from GUI.ExampleDatabaseTableWindow import ExampleDatabaseTableWindow

# from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget import *
from GUI.UI.qtimeline import *

from GUI.UI.ExtendedTracksContainerWidget import ExtendedTracksContainerWidget
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Videos import *
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Partition import TrackContextConfig, TimelineTrackDrawingWidget_Partition
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_AnnotationComments import *

# from app.database.SqliteEventsDatabase import load_video_events_from_database
from app.database.SqlAlchemyDatabase import load_annotation_events_from_database, save_annotation_events_to_database, create_TimestampedAnnotation

from GUI.UI.VideoPlayer.MainVideoPlayerWindow import *
from GUI.SetupWindow.SetupWindow import *

from GUI.Model.Events.PhoDurationEvent_Video import PhoDurationEvent_Video

from GUI.UI.TimelineHeaderWidget.TimelineHeaderWidget import TimelineHeaderWidget


class GlobalTimeAdjustmentOptions(Enum):
        ConstrainGlobalToVideoTimeRange = 1 # adjusts the global start and end times for the timeline to the range of the loaded videos.
        ConstrainVideosShownToGlobal = 2 #  keeps the global the same, and only shows the videos within the global start and end range
        ConstantOffsetFromMostRecentVideo = 3  # adjusts the global to a fixed time prior to the end of the most recent video.



"""
self.activeScaleMultiplier: this multipler determines how many times longer the contents of the scrollable viewport are than the viewport width itself.

"""
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

        self.shouldUseTrackHeaders = True

        self.partitionTrackContextsArray = [TrackContextConfig('Behavior'), TrackContextConfig('Unknown')]

        # self.videoInfoObjects = load_video_events_from_database(self.database_connection.get_path(), as_videoInfo_objects=True)
        self.videoInfoObjects = []
        self.trackVideoEventDisplayObjects = dict()

        self.reloadModelFromDatabase()

        self.build_video_display_events()

        self.videoPlayerWindow = None
        self.helpWindow = None
        self.setupWindow = None
        self.videoTreeWindow = None
        self.databaseBrowserUtilityWindow = None
    

        self.setMouseTracking(True)

        self.minimumVideoTrackHeight = 50
        # self.minimumVideoTrackHeight = 25


        self.initUI()
        # self.show() # Show the GUI

        overlappingVideoEvents = self.mainVideoTrack.find_overlapping_events()
        for aTuple in overlappingVideoEvents:
            print(aTuple)
        # print(overlappingVideoEvents)

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
            self.ui.actionVideo_FIle_ShowListWindow.triggered.connect(self.handle_showVideoTreeWindow)
            self.ui.actionShowDatabase_Table_BrowserWindow.triggered.connect(self.handle_showDatabaseBrowserUtilityWindow)
            
            ## Setup Zoom:
            self.ui.actionZoom_In.triggered.connect(self.on_zoom_in)
            self.ui.actionZoom_Default.triggered.connect(self.on_zoom_home)
            self.ui.actionZoom_CurrentVideo.triggered.connect(self.on_zoom_current_video)
            self.ui.actionZoom_Out.triggered.connect(self.on_zoom_out)

            ## Navigation Menus:
            # on_jump_to_start, on_jump_previous, on_jump_next, on_jump_to_end
            self.ui.actionJump_to_Start.triggered.connect(self.on_jump_to_start)
            self.ui.actionJump_to_Previous.triggered.connect(self.on_jump_previous)
            self.ui.actionJump_to_Active_Video_Playhead.triggered.connect(self.on_jump_to_video_playhead)
            self.ui.actionJump_to_Next.triggered.connect(self.on_jump_next)
            self.ui.actionJump_to_End.triggered.connect(self.on_jump_to_end)


            # Operations Menus:
            self.ui.actionCut_at_Active_Video_Playhead.triggered.connect(self.on_cut_at_active_timeline_playhead)

            # Window Footer Toolbar
            self.ui.toolButton_ZoomIn.setDefaultAction(self.ui.actionZoom_In)            
            self.ui.toolButton_CurrentVideo.setDefaultAction(self.ui.actionZoom_CurrentVideo)
            self.ui.toolButton_ZoomOut.setDefaultAction(self.ui.actionZoom_Out)

            self.ui.toolButton_ScrollToStart.setDefaultAction(self.ui.actionJump_to_Start)
            self.ui.toolButton_ScrollToPrevious.setDefaultAction(self.ui.actionJump_to_Previous)
            self.ui.toolButton_activeVideoPlayHead.setDefaultAction(self.ui.actionJump_to_Active_Video_Playhead)
            self.ui.toolButton_ScrollToNext.setDefaultAction(self.ui.actionJump_to_Next)
            self.ui.toolButton_ScrollToEnd.setDefaultAction( self.ui.actionJump_to_End)


        def initUI_timelineTracks(self):
            # Timeline Numberline track:
            masterTimelineDurationSeconds = self.totalDuration.total_seconds()
            self.timelineMasterTrackWidget = QTimeLine(masterTimelineDurationSeconds, minimumWidgetWidth)
            self.timelineMasterTrackWidget.setMouseTracking(True)
            self.timelineMasterTrackWidget.hoverChanged.connect(self.handle_timeline_hovered_position_update_event)
            self.timelineMasterTrackWidget.positionChanged.connect(self.handle_timeline_position_update_event)

        
            # Video Tracks
            ## TODO: The video tracks must set:
            self.videoFileTrackWidgets = []

            # self.trackVideoEventDisplayObjects[1]
            # self.allVideoEventDisplayObjects.filter()
            currTrackIndex = 0
            currTrackBBID = 0
            self.mainVideoTrack = TimelineTrackDrawingWidget_Videos(currTrackIndex, self.trackVideoEventDisplayObjects[currTrackBBID][0], [], self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
            self.mainVideoTrack.set_track_title_label('BBID: {0}, originals'.format(currTrackBBID))
            self.videoFileTrackWidgets.append(self.mainVideoTrack)

            currTrackIndex = currTrackIndex + 1
            self.labeledVideoTrack = TimelineTrackDrawingWidget_Videos(currTrackIndex, self.trackVideoEventDisplayObjects[currTrackBBID][1], [], self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
            self.labeledVideoTrack.set_track_title_label('BBID: {0}, labeled'.format(currTrackBBID))
            self.videoFileTrackWidgets.append(self.labeledVideoTrack)

            currTrackIndex = currTrackIndex + 1
            currTrackBBID = currTrackBBID + 1
            self.mainVideoTrack1 = TimelineTrackDrawingWidget_Videos(currTrackIndex, self.trackVideoEventDisplayObjects[currTrackBBID][0], [], self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
            self.mainVideoTrack1.set_track_title_label('BBID: {0}, originals'.format(currTrackBBID))
            self.videoFileTrackWidgets.append(self.mainVideoTrack1)

            currTrackIndex = currTrackIndex + 1
            self.labeledVideoTrack1 = TimelineTrackDrawingWidget_Videos(currTrackIndex, self.trackVideoEventDisplayObjects[currTrackBBID][1], [], self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
            self.labeledVideoTrack1.set_track_title_label('BBID: {0}, labeled'.format(currTrackBBID))
            self.videoFileTrackWidgets.append(self.labeledVideoTrack1)

            # Other Tracks:
            self.eventTrackWidgets = []

            # Annotation Comments track:
            currTrackIndex = currTrackIndex + 1
            self.annotationCommentsTrackWidget = TimelineTrackDrawingWidget_AnnotationComments(currTrackIndex, [], [], self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
            self.eventTrackWidgets.append(self.annotationCommentsTrackWidget)

            # Partition tracks:
            currTrackIndex = currTrackIndex + 1
            self.partitionsTrackWidget = TimelineTrackDrawingWidget_Partition(currTrackIndex, None, [], self.totalStartTime, self.totalEndTime, self.database_connection, self.partitionTrackContextsArray[0])
            self.eventTrackWidgets.append(self.partitionsTrackWidget)

            currTrackIndex = currTrackIndex + 1
            self.partitionsTwoTrackWidget = TimelineTrackDrawingWidget_Partition(currTrackIndex, None, [], self.totalStartTime, self.totalEndTime, self.database_connection, self.partitionTrackContextsArray[1])
            self.eventTrackWidgets.append(self.partitionsTwoTrackWidget)

            # Build the bottomPanelWidget
            self.extendedTracksContainer = ExtendedTracksContainerWidget(masterTimelineDurationSeconds, minimumWidgetWidth, self)
            self.extendedTracksContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.extendedTracksContainer.setAutoFillBackground(True)
            self.extendedTracksContainer.setMouseTracking(True)
            self.extendedTracksContainer.hoverChanged.connect(self.handle_timeline_hovered_position_update_event)

            # bind to self to detect changes in either child
            self.timelineMasterTrackWidget.hoverChanged.connect(self.on_playhead_hover_position_updated)
            self.extendedTracksContainer.hoverChanged.connect(self.on_playhead_hover_position_updated)

            # self.timelineMasterTrackWidget.hoverChanged.connect(self.extendedTracksContainer.on_update_hover)
            
            #Layout of Extended Tracks Container Widget
            self.extendedTracksContainerVboxLayout = QVBoxLayout(self)
            self.extendedTracksContainerVboxLayout.addStretch(1)
            self.extendedTracksContainerVboxLayout.addSpacing(2.0)
            self.extendedTracksContainerVboxLayout.setContentsMargins(0,0,0,0)

            self.extendedTracksContainerVboxLayout.addWidget(self.timelineMasterTrackWidget)
            self.timelineMasterTrackWidget.setMinimumSize(minimumWidgetWidth, 50)
            self.timelineMasterTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            
            
        def initUI_layout(self):

            self.videoFileTrackWidgetHeaders = dict()
            # Loop through the videoFileTrackWidgets and add them
            for i in range(0, len(self.videoFileTrackWidgets)):
                currVideoTrackWidget = self.videoFileTrackWidgets[i]
                # Video track specific setup
                currVideoTrackWidget.selection_changed.connect(self.handle_child_selection_event)
                currVideoTrackWidget.hover_changed.connect(self.handle_child_hover_event)
                currVideoTrackWidget.setMouseTracking(True)
                currVideoTrackWidget.shouldDismissSelectionUponMouseButtonRelease = False
                currVideoTrackWidget.itemSelectionMode = ItemSelectionOptions.SingleSelection

                if self.shouldUseTrackHeaders:
                    # currHeaderIncludedTrackLayout = QGridLayout(self.extendedTracksContainer)
                    currHeaderIncludedTrackLayout = QGridLayout(self)
                    currHeaderIncludedTrackLayout.setSpacing(0)
                    currHeaderIncludedTrackLayout.setContentsMargins(0,0,0,0)

                    # label gets positioned above textBrowser and is an overlay
                    currHeaderIncludedContainer = QWidget(self)

                    currHeaderWidget = TimelineHeaderWidget(currVideoTrackWidget.trackID, parent=self)
                    #Layout of Extended Tracks Container Widget
                    # currHeaderIncludedTrackHboxLayout = QHBoxLayout(self)
                    # currHeaderIncludedTrackHboxLayout.addStretch(1)
                    # currHeaderIncludedTrackHboxLayout.addSpacing(0.0)
                    # currHeaderIncludedTrackHboxLayout.setContentsMargins(0,0,0,0)
                    # currHeaderIncludedTrackHboxLayout.addWidget(currHeaderWidget)

                    currHeaderWidget.setMinimumSize(50, self.minimumVideoTrackHeight)
                    # currHeaderWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                    # currHeaderWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                    currHeaderWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                    currHeaderWidget.toggleCollapsed.connect(self.on_track_header_toggle_collapse_activated)
                    currHeaderWidget.showOptions.connect(self.on_track_header_show_options_activated)
                    currHeaderWidget.refresh.connect(self.on_track_header_refresh_activated)

                    # self.videoFileTrackWidgetHeaders.append(currHeaderWidget)
                    self.videoFileTrackWidgetHeaders[currVideoTrackWidget.trackID] = currHeaderWidget

                    # currHeaderIncludedTrackHboxLayout.addWidget(currVideoTrackWidget)
                    # currHeaderIncludedContainer.setLayout(currHeaderIncludedTrackHboxLayout)
                    # self.extendedTracksContainerVboxLayout.addWidget(currHeaderIncludedContainer)
                    # currHeaderIncludedContainer.setMinimumSize(minimumWidgetWidth+50, self.minimumVideoTrackHeight)
                    # currHeaderIncludedContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                    currHeaderIncludedTrackLayout.addWidget(currVideoTrackWidget, 0, 0, Qt.AlignLeft|Qt.AlignTop)
                    currVideoTrackWidget.setMinimumSize(minimumWidgetWidth, self.minimumVideoTrackHeight)
                    currVideoTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                    currHeaderIncludedTrackLayout.addWidget(currHeaderWidget, 0, 0, Qt.AlignLeft|Qt.AlignTop)

                    currHeaderIncludedContainer.setLayout(currHeaderIncludedTrackLayout)

                    # currHeaderIncludedContainer.setMinimumSize(minimumWidgetWidth, self.minimumVideoTrackHeight)
                    # currHeaderIncludedContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                    self.extendedTracksContainerVboxLayout.addWidget(currHeaderIncludedContainer)

                else:
                    self.extendedTracksContainerVboxLayout.addWidget(currVideoTrackWidget)
                    currVideoTrackWidget.setMinimumSize(minimumWidgetWidth,self.minimumVideoTrackHeight)
                    currVideoTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                # General Layout:




            self.eventTrackWidgetHeaders = dict()

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



        desiredWindowWidth = 900
        self.resize( desiredWindowWidth, 800 )
        
        self.setWindowFilePath(self.database_connection.get_path())

        # Setup the menubar
        initUI_initMenuBar(self)

        # minimumWidgetWidth = 500
        minimumWidgetWidth = self.get_minimum_track_width()

        # Toolbar
        # self.ui.dockWidget_FooterToolbar
        self.ui.doubleSpinBox_currentZoom.setValue(self.activeScaleMultiplier)
        # self.ui.doubleSpinBox_currentZoom.valueChanged.connect(self.on_zoom_custom)
        self.ui.doubleSpinBox_currentZoom.editingFinished.connect(self.on_finish_editing_zoom_custom)

        # Video Player Container: the container that holds the video player
        self.videoPlayerContainer = QtWidgets.QWidget()
        self.videoPlayerContainer.setMouseTracking(True)
        ## TODO: Add the video player to the container.
        ## TODO: Needs a layout
        
        ## Define WIDGETS:

        ## Timeline Tracks:
        initUI_timelineTracks(self)
        

        #Layout of Main Window:
        initUI_layout(self)

        # Complete setup
        self.setCentralWidget( self.verticalSplitter )
        self.setMouseTracking(True)
        self.statusBar()

        self.setWindowTitle('Pho Timeline Test Drawing Window')

        self.ui.lblActiveViewportDuration.setText(str(self.get_active_viewport_duration()))
        self.ui.lblActiveTotalTimelineDuration.setText(str(self.totalDuration))
        self.ui.lblActiveViewportOffsetAbsolute.setText(str(0.0))

        # Cursor tracking
        self.cursorX = 0.0
        self.cursorY = 0.0
        #self.cursorTraceRect = QRect(0,0,0,0)

    def reloadModelFromDatabase(self):
        # Context objects for children tracks
        self.contextsDict = self.database_connection.load_contexts_from_database()
        self.subcontexts = self.database_connection.load_subcontexts_from_database()

        for (index, aPartitionTrackContextInfoObj) in enumerate(self.partitionTrackContextsArray):
            newContext = self.contextsDict[aPartitionTrackContextInfoObj.get_context_name()]
            newSubcontext = newContext.subcontexts[aPartitionTrackContextInfoObj.get_subcontext_index()]
            aPartitionTrackContextInfoObj.update_on_load(newContext, newSubcontext)

        # Video file objects for video tracks
        self.videoFileRecords = self.database_connection.load_video_file_info_from_database()
        self.videoInfoObjects = []
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
        # self.trackVideoEventDisplayObjects = [[], []]

        self.trackVideoEventDisplayObjects = dict()
        # self.trackVideoEventDisplayObjects = {1:([], []), 2:([], []), 6:([], []), 7:([], []), 9:([], []), 10:([], [])}

        for (index, videoInfoItem) in enumerate(self.videoInfoObjects):
            videoDates.append(videoInfoItem.startTime)
            videoEndDates.append(videoInfoItem.endTime)
            currExtraInfoDict = videoInfoItem.get_output_dict()
            # Event Generation
            currEvent = PhoDurationEvent_Video(videoInfoItem.startTime, videoInfoItem.endTime, videoInfoItem.fullName, QColor(51,204,255), currExtraInfoDict)
            currRecord = self.videoFileRecords[index]

            self.allVideoEventDisplayObjects.append(currEvent)

            currBBID = currRecord.get_behavioral_box_id()
            if currBBID is not None:
                # If we have a valid behavioral box ID

                # Create the key if we need it
                if currBBID not in self.trackVideoEventDisplayObjects.keys():
                    self.trackVideoEventDisplayObjects[currBBID] = ([], [])
                    print("Adding BBID: {0}".format(currBBID))

                if videoInfoItem.is_original_video:
                    self.trackVideoEventDisplayObjects[currBBID][0].append(currEvent)
                else:
                    self.trackVideoEventDisplayObjects[currBBID][1].append(currEvent)


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


    def percent_to_offset(self, percent_offset):
        event_x = percent_offset * (self.width() * self.activeScaleMultiplier)
        return event_x

    def duration_to_offset(self, duration_offset):
        percent_x = duration_offset / self.totalDuration
        event_x = self.percent_to_offset(percent_x)
        return event_x

    def datetime_to_offset(self, newDatetime):
        duration_offset = newDatetime - self.totalStartTime
        event_x = self.duration_to_offset(duration_offset)
        return event_x



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
        print("TimelineDrawingWindow.keyPressEvent(): {0}".format(str(event.key())))


        if event.key() == Qt.Key_Space:
            try:
                self.videoPlayerWindow.key_handler(event)
                return
            except AttributeError as e:
                print("Couldn't get videoPlayerWindow! Error:", e)
                pass
            
        if event.key() == Qt.Key_P:
            try:
                self.videoPlayerWindow.key_handler(event)
                return
            except AttributeError as e:
                print("Couldn't get videoPlayerWindow! Error:", e)
                pass
            
            
        # TODO: pass to all children
        # self.mainVideoTrack.on_key_pressed(event)
        for (anIndex, aTimelineVideoTrack) in enumerate(self.videoFileTrackWidgets):
            if (aTimelineVideoTrack.wantsKeyboardEvents):
                aTimelineVideoTrack.on_key_pressed(event)

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

        for (anIndex, aTimelineVideoTrack) in enumerate(self.videoFileTrackWidgets):
            potentially_hovered_child_object = aTimelineVideoTrack.hovered_object
            if potentially_hovered_child_object:
                relative_duration_offset = potentially_hovered_child_object.compute_relative_offset_duration(datetime)
                text = text + ' -- relative to duration: {0}'.format(relative_duration_offset)
                break

        # TODO: Need to use offset into scroll view instead of window?
        
        # Exhaustive event forwarding for all track widgets
        for (anIndex, aTimelineTrack) in enumerate(self.eventTrackWidgets):
            if (aTimelineTrack.wantsMouseEvents):
                aTimelineTrack.on_mouse_moved(event)


        self.statusBar().showMessage(text)

    def wheelEvent(self, event):
        # print("mouse wheel event! {0}".format(str(event)))
        hsb=self.timelineScroll.horizontalScrollBar()
        dy=((-event.angleDelta().y()/8)/15)*hsb.singleStep()
        hsb.setSliderPosition(hsb.sliderPosition()+dy)

    ## Zoom in/default/out events
    def get_minimum_track_width(self):
        return  (self.width() * self.activeScaleMultiplier)

    # Sets the self.activeScaleMultipler based on the desiredMinimumWidth
    # returns the new active scale multiplier
    def set_minimum_track_width(self, desiredMinimumWidth):
        newActiveScaleMultiplier = desiredMinimumWidth / self.width()
        self.activeScaleMultiplier = newActiveScaleMultiplier
        return newActiveScaleMultiplier

    def get_viewport_width(self):
        return self.timelineScroll.width()

    # Returns the percent of the total duration that the active viewport is currently displaying
    def get_active_viewport_duration_percent_viewport_total(self):
        return (float(self.get_viewport_width()) / float(self.get_minimum_track_width()))
    
    def set_active_viewport_duration_percent_viewport_total(self, desiredPercent):
        desiredMinimumWidth = (float(self.get_viewport_width()) / float(desiredPercent))
        return self.set_minimum_track_width(desiredMinimumWidth)

    # Returns the duration of the currently displayed viewport
    def get_active_viewport_duration(self):
        currPercent = self.get_active_viewport_duration_percent_viewport_total()
        return (currPercent * self.totalDuration)

    def set_active_viewport_duration(self, desiredDuration):
        desiredPercent = desiredDuration / self.totalDuration
        return self.set_active_viewport_duration_percent_viewport_total(desiredPercent)



    # Given the percent offset of the total duration, gets the x-offset for the timeline tracks (not the viewport, its contents)
    def percent_offset_to_track_offset(self, track_percent):
        return float(self.get_minimum_track_width()) * float(track_percent)

    ## Datetime functions copied from the versions created for the PhoDurationEvent class
    # returns true if the absolute_datetime falls within the current entire timeline. !Not the viewport!
    def contains_date(self, absolute_datetime):
        return ((self.totalStartTime <= absolute_datetime) and (self.totalEndTime >= absolute_datetime))

    # Returns the duration of the time relative to this timeline.
    def compute_relative_offset_duration(self, time):
        relative_offset_duration = time - self.totalStartTime
        return relative_offset_duration

    # Returns the absolute (wall/world) time for a relative_duration into the timeline
    def compute_absolute_time(self, relative_duration):
        return (self.totalStartTime + relative_duration)


    ## Timeline ZOOMING:
    def on_zoom_in(self):
        self.activeScaleMultiplier = min(TimelineDrawingWindow.MaxZoomLevel, (self.activeScaleMultiplier + TimelineDrawingWindow.ZoomDelta))
        self.on_active_zoom_changed()

    def on_zoom_home(self):
        self.activeScaleMultiplier = TimelineDrawingWindow.DefaultZoom
        self.on_active_zoom_changed()

    def on_zoom_current_video(self):
        # on_zoom_current_video(): zooms the viewport to fit the current video
        print("on_zoom_current_video()")
        # Gets the current video

        selected_video_event_obj = self.mainVideoTrack.get_selected_duration_obj()
        if selected_video_event_obj is None:
            print("no video selected!")
            return
        
        newViewportStartTime = selected_video_event_obj.startTime
        newViewportEndTime = selected_video_event_obj.endTime
        newViewportDuration = selected_video_event_obj.computeDuration()

        if newViewportDuration is None:
            print("selected video has a None duration!")
            return
        else:
            self.set_viewport_to_range(newViewportStartTime, newViewportEndTime)

        return

    def on_zoom_out(self):
        self.activeScaleMultiplier = max(TimelineDrawingWindow.MinZoomLevel, (self.activeScaleMultiplier - TimelineDrawingWindow.ZoomDelta))
        self.on_active_zoom_changed()
        
    def on_finish_editing_zoom_custom(self):
        print("on_finish_editing_zoom_custom()")
        double_newZoom = self.ui.doubleSpinBox_currentZoom.value()
        print("new_zoom: {0}".format(double_newZoom))
        self.activeScaleMultiplier = double_newZoom
        self.on_active_zoom_changed()

    # Called after self.activeScaleMultiplier is changed to update everything else
    def on_active_zoom_changed(self):
        self.ui.doubleSpinBox_currentZoom.blockSignals(True)
        self.ui.doubleSpinBox_currentZoom.setValue(self.activeScaleMultiplier)
        self.ui.doubleSpinBox_currentZoom.blockSignals(False)
        self.ui.lblActiveTotalTimelineDuration.setText(str(self.totalDuration))
        self.on_active_viewport_changed()
        self.resize_children_on_zoom()
        # self.refresh_child_widget_display()

    def on_active_viewport_changed(self):
        self.ui.lblActiveViewportDuration.setText(str(self.get_active_viewport_duration()))
        self.ui.lblActiveViewportOffsetAbsolute.setText(str(self.get_viewport_percent_scrolled()))

    def resize_children_on_zoom(self):
        newMinWidth = self.get_minimum_track_width()
        self.extendedTracksContainer.setFixedWidth(newMinWidth)
        self.update()

    ## Navigation:
    
    # Returns the current perent scrolled the viewport is through the entire timeline.
    def get_viewport_percent_scrolled(self):
        return (self.timelineScroll.horizontalScrollBar().value() / (self.timelineScroll.horizontalScrollBar().maximum() - self.timelineScroll.horizontalScrollBar().minimum()))


    # Scrolls the viewport to the desired percent_scrolled of entire timeline.
    def set_viewport_percent_scrolled(self, percent_scrolled):
        scrollbar_scroll_relative_offset = (percent_scrolled * (self.timelineScroll.horizontalScrollBar().maximum() - self.timelineScroll.horizontalScrollBar().minimum()))
        scrollbar_offset = scrollbar_scroll_relative_offset + self.timelineScroll.horizontalScrollBar().minimum()
        self.timelineScroll.horizontalScrollBar().setValue(scrollbar_offset)

    # Moves and sizes the current viewport's position such that it's start position is aligned with a specific start_time and its end position is aligned with a specific end_time. This also adjusts the zoom!
    def set_viewport_to_range(self, start_time, end_time):
        newViewportDuration = end_time - start_time
        if newViewportDuration is None:
            print("selected range has a None duration!")
            return False
        
        # Compute appropriate zoom.
        newZoom = self.set_active_viewport_duration(newViewportDuration)
        self.on_active_zoom_changed()
        return self.sync_active_viewport_start_to_datetime(start_time)


    # Moves the current viewport's position such that it's start position is aligned with a specific start_time
    def sync_active_viewport_start_to_datetime(self, start_time):
        # get the viewport's end time
        end_time = start_time + self.get_active_viewport_duration()
        return self.sync_active_viewport_end_to_datetime(end_time)


    # Moves the current viewport's position such that it's end position is aligned with a specific end_time
    def sync_active_viewport_end_to_datetime(self, end_time):
        if end_time > self.totalEndTime:
            print("Error: end_time > self.totalEndTime!")
            return False

         # Compute appropriate offset:
        found_x_offset = self.datetime_to_offset(end_time)
        self.timelineScroll.ensureVisible(found_x_offset, 0, 0, 0)
        self.on_active_zoom_changed()
        return True
        
        
    ## Timeline Navigation:
    def on_jump_to_start(self):
        print("on_jump_to_start()")
        self.timelineScroll.horizontalScrollBar().setValue(self.timelineScroll.horizontalScrollBar().minimum())
        self.on_active_zoom_changed()
        
    def on_jump_previous(self):
        print("on_jump_previous()")
        # self.activeScaleMultiplier = TimelineDrawingWindow.DefaultZoom
        self.on_active_zoom_changed()

    # Zoom the timeline to the current video playhead position
    def on_jump_to_video_playhead(self):
        try:
            active_movie_link = self.videoPlayerWindow.get_movie_link()
            if active_movie_link is None:
                print("No movie link!")
                return

            playbackPlayheadDatetime = active_movie_link.get_active_absolute_datetime()
            if playbackPlayheadDatetime is None:
                print("Movie link has no active playbackPlayheadDatetime!")
                return

            self.sync_active_viewport_start_to_datetime(playbackPlayheadDatetime)

        except AttributeError as e:
            print("Couldn't get movie link's active playbackPlayheadDatetime! Error:", e)
            pass
        
        return

    def on_jump_next(self):
        # Jump to the next available video in the video track
        # TODO: could highlight the video that's being jumped to.
        print("on_jump_next()")
        offset_x = self.percent_offset_to_track_offset(self.get_viewport_percent_scrolled())
        offset_datetime = self.offset_to_datetime(offset_x)
        # next_video_tuple: (index, videoObj) pair
        next_video_tuple = self.videoFileTrackWidgets[0].find_next_event(offset_datetime)
        if next_video_tuple is None:
            print("next_video_tuple is none!")
            return
        else:
            print("next_video_tuple is {0}".format(next_video_tuple[0]))

        found_start_date = next_video_tuple[1].startTime
        self.sync_active_viewport_start_to_datetime(found_start_date)
        return

    def on_jump_to_end(self):
        print("on_jump_to_end()")
        # verticalScrollBar()->setValue(ui->scrollArea->verticalScrollBar()->maximum());
        self.timelineScroll.horizontalScrollBar().setValue(self.timelineScroll.horizontalScrollBar().maximum())
        self.on_active_zoom_changed()



    ## Other windows:

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
        if (not (self.videoPlayerWindow is None)):
            self.videoPlayerWindow.show()
        else:
            # Create a new videoPlayerWindow window
            self.videoPlayerWindow = MainVideoPlayerWindow(parent=self)
            self.videoPlayerWindow.show()

    def try_set_video_player_window_url(self, url):
        #TODO: temp: set the videoPlayerWindow to None to ensure that a new one is created. Note that setting it to None doesn't actually close the old one.
        self.videoPlayerWindow = None


        if (not (self.videoPlayerWindow is None)):
            print("Using existing Video Player Window...")
            self.videoPlayerWindow.set_timestamp_filename(r"C:\Users\halechr\repo\looper\testdata\NewTimestamps.tmsp")
            self.videoPlayerWindow.set_video_filename(url)

            # self.videoPlayerWindow.show()
        else:
            # Create a new videoPlayerWindow window
            print("Creating new Video Player Window...")
            try:
                self.videoPlayerWindow = MainVideoPlayerWindow(parent=self)
            except Exception as e:
                print("Error Spawning Video Window:", e)
                return False

            
            try:
                self.videoPlayerWindow.set_timestamp_filename(r"C:\Users\halechr\repo\looper\testdata\NewTimestamps.tmsp")
            except Exception as e:
                print("Error Setting timestamp filename for Video Window:", e)
                return False


            try:
                self.videoPlayerWindow.set_video_filename(url)
            except Exception as e:
                print("Error Setting video filename for Video Window:", e)
                return False

            return True


    # Shows the Video File Tree window:
    def handle_showVideoTreeWindow(self):
        if self.videoTreeWindow:
            self.videoTreeWindow.set_database_connection(self.database_connection)
            self.videoTreeWindow.show()
        else:
            # Create a new setup window
            self.videoTreeWindow = MainObjectListsWindow(self.database_connection, [])
            self.videoTreeWindow.show()

        self.reposition_videoTreeWindow()

    def reposition_videoTreeWindow(self):
        if self.videoTreeWindow is None:
            return
        self.mainWindowGeometry = self.frameGeometry()
        self.sideListWindowGeometry = self.videoTreeWindow.frameGeometry()
        self.sideListWindowGeometry.moveTopRight(self.mainWindowGeometry.topLeft())
        self.videoTreeWindow.move(self.sideListWindowGeometry.topLeft())


    # Shows the databaseBrowserUtilityWindow: a database table viewer/editor
    def handle_showDatabaseBrowserUtilityWindow(self):
        if self.databaseBrowserUtilityWindow:
            self.databaseBrowserUtilityWindow.set_database_connection(self.database_connection)
            self.databaseBrowserUtilityWindow.show()
        else:
            # Create a new setup window
            self.databaseBrowserUtilityWindow = ExampleDatabaseTableWindow(self.database_connection)
            self.databaseBrowserUtilityWindow.show()

        
        

    # @pyqtSlot(int, int)
    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_selection_event(self, trackIndex, trackObjectIndex):
        text = "handle_child_selection_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
        print(text)
        # if trackIndex == TimelineDrawingWindow.static_VideoTrackTrackID:

        # If it's the video track
        if trackObjectIndex == TimelineTrackDrawingWidget_Videos.static_TimeTrackObjectIndex_NoSelection:
            # No selection, just clear the filters
            # for i in range(0, len(self.eventTrackWidgets)):
            #     currWidget = self.eventTrackWidgets[i]
            #     currWidget.set_active_filter(self.totalStartTime, self.totalEndTime)

            for aVideoTrackIndex in range(0, len(self.videoFileTrackWidgets)):
                currVideoTrackWidget = self.videoFileTrackWidgets[aVideoTrackIndex]
                # currVideoTrackWidget.set_active_filter(self.totalStartTime, self.totalEndTime)
                currVideoTrackWidget.deselect_all()
                currVideoTrackWidget.update()
            
            
        else:
            # Get the selected video object
            # currHoveredObject = self.mainVideoTrack.hovered_object

            # currSelectedObjectIndex = self.mainVideoTrack.selected_duration_object_indicies[0]
            currSelectedObjectIndex = trackObjectIndex
            currActiveVideoTrack = self.videoFileTrackWidgets[trackIndex]
            currSelectedObject = currActiveVideoTrack.durationObjects[trackObjectIndex]
            
            # Deselect any other video timelines
            for aVideoTrackIndex in range(0, len(self.videoFileTrackWidgets)):
                if (aVideoTrackIndex == trackIndex):
                    # Skip the active track
                    continue
                else:
                    currVideoTrackWidget = self.videoFileTrackWidgets[aVideoTrackIndex]
                    currVideoTrackWidget.deselect_all()
                    currVideoTrackWidget.update()

            if currSelectedObject:
                selected_video_path = currSelectedObject.get_video_url()
                print(selected_video_path)
                currActiveVideoTrack.set_now_playing(trackObjectIndex)

                if currSelectedObject.is_video_url_accessible():
                    self.try_set_video_player_window_url(str(selected_video_path))
                    self.videoPlayerWindow.movieLink = DataMovieLinkInfo(currSelectedObject, self.videoPlayerWindow, self, parent=self)
                else:
                    print("video file is inaccessible. Not opening the video player window")
                    if self.videoPlayerWindow is not None:
                        self.videoPlayerWindow.try_set_video_player_window_url(None)
                        # Close any active movieLinks since there can't be a selection here. 
                        self.videoPlayerWindow.movieLink = None

            else:
                print("invalid object selected!!")

            # Iterate through the timeline tracks to filter based on the video.
            # for i in range(0, len(self.eventTrackWidgets)):
            #     currWidget = self.eventTrackWidgets[i]
            #     currWidget.set_active_filter(currHoveredObject.startTime, currHoveredObject.endTime)


    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_hover_event(self, trackIndex, trackObjectIndex):
        text = "handle_child_hover_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
        # print(text)
        return

    def handle_timeline_hovered_position_update_event(self, x):
        # print("handle_timeline_hovered_position_update_event({0})".format(x))
        pass

    def handle_timeline_position_update_event(self, x):
        # print("handle_timeline_position_update_event({0})".format(x))
        pass

    def refresh_child_widget_display(self):
        for i in range(0, len(self.eventTrackWidgets)):
            currWidget = self.eventTrackWidgets[i]
            currWidget.update()

    @pyqtSlot(float)
    def on_video_playback_position_updated(self, timeline_percent_offset):
        # print("on_video_playback_position_updated({0})".format(str(timeline_percent_offset)))
        timeline_x_offset = self.percent_offset_to_track_offset(timeline_percent_offset)

        self.timelineMasterTrackWidget.blockSignals(True)
        self.extendedTracksContainer.blockSignals(True)

        self.timelineMasterTrackWidget.on_update_video_line(timeline_x_offset)
        self.extendedTracksContainer.on_update_video_line(timeline_x_offset)
        
        self.extendedTracksContainer.blockSignals(False)
        self.timelineMasterTrackWidget.blockSignals(False)

    # Called when the timeline or background container of the track view is hovered
    # updates its children views, but doesn't currently update the movie play position.
    @pyqtSlot(int)
    def on_playhead_hover_position_updated(self, x):
        # print("on_playhead_hover_position_updated({0})".format(str(x)))
        self.timelineMasterTrackWidget.blockSignals(True)
        self.extendedTracksContainer.blockSignals(True)

        self.timelineMasterTrackWidget.on_update_hover(x)
        self.extendedTracksContainer.on_update_hover(x)

        # if(self.videoPlayerWindow):
        #     movie_link = self.videoPlayerWindow.get_movie_link()
        #     if (movie_link is not None):
        #         ## TODO NOW: 
        #         print("NOT YET IMPLEMENTED: Timeline to Video playback sync")

        #         # Check if convertedDatetime is in range.
                
        #         #convertedDatetime: the datetime
        #         # movie_link.update_timeline_playhead_position(convertedDatetime)


        self.extendedTracksContainer.blockSignals(False)
        self.timelineMasterTrackWidget.blockSignals(False)
        

        # self.extendedTracksContainer.on_update_hover




    ## Track Operations:
    def on_cut_at_active_timeline_playhead(self):
        print("on_cut_at_active_timeline_playhead(...)")
        try:
            active_movie_link = self.videoPlayerWindow.get_movie_link()
            if active_movie_link is None:
                print("No movie link!")
                return

            playbackPlayheadDatetime = active_movie_link.get_active_absolute_datetime()
            if playbackPlayheadDatetime is None:
                print("Movie link has no active playbackPlayheadDatetime!")
                return

            # self.sync_active_viewport_start_to_datetime(playbackPlayheadDatetime) #jump there.
            self.on_partition_cut_at(playbackPlayheadDatetime) #then cut

        except AttributeError as e:
            print("Couldn't get movie link's active playbackPlayheadDatetime! Error:", e)
            pass
        
        return
        
    
    # Creates a cut on the partition track at the specified time
    def on_partition_cut_at(self, cut_datetime):
        print("on_partition_cut_at({0})".format(cut_datetime))
        self.partitionsTrackWidget.try_cut_partition(cut_datetime)


    # Creates a new annotation comment on the appropriate track at the specified time
    def on_comment_create_at(self, comment_datetime):
        print("on_comment_create_at({0})".format(comment_datetime))
        # self.partitionsTrackWidget.try_cut_partition(comment_datetime)
        


    # Track Header Operations:
    @pyqtSlot(int, bool)
    def on_track_header_toggle_collapse_activated(self, trackID, isCollapsed):
        print("on_track_header_toggle_collapse({0}, {1})".format(trackID, isCollapsed))
        currHeader = self.videoFileTrackWidgetHeaders[trackID]
        currHeader.perform_collapse()
        # currHeader.setHidden(True)

    @pyqtSlot(int)
    def on_track_header_show_options_activated(self, trackID):
        print("on_track_header_show_options({0})".format(trackID))
        
    @pyqtSlot(int)
    def on_track_header_refresh_activated(self, trackID):
        print("on_track_header_refresh_activated({0})".format(trackID))