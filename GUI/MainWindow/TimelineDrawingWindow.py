# EventsDrawingWindow.py
# Draws the main window containing several EventTrackDrawingWidgets

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QGridLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QAbstractSlider, QAbstractScrollArea, QDialog, QLabel
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from app.database.entry_models.db_model import Animal, BehavioralBox, Context, Experiment, Labjack, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent, CategoricalDurationLabel, VideoFile

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWindow

from GUI.HelpWindow.HelpWindowFinal import *
from GUI.MainObjectListsWindow.MainObjectListsWindow import *
from GUI.ExampleDatabaseTableWindow import ExampleDatabaseTableWindow

from GUI.Model.ReferenceLines.ReferenceLineManager import ReferenceMarkerManager, IndicatorLineMixin
# from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget import *
from GUI.UI.qtimeline import *

from GUI.UI.ExtendedTracksContainerWidget import ExtendedTracksContainerWidget
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Videos import *
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_Partition import TrackContextConfig, TimelineTrackDrawingWidget_Partition
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_AnnotationComments import *

# from app.database.SqliteEventsDatabase import load_video_events_from_database
from app.database.SqlAlchemyDatabase import load_annotation_events_from_database, save_annotation_events_to_database, create_TimestampedAnnotation

from GUI.UI.VideoPlayer.VideoPlayerWidget import VideoPlayerWidget
from GUI.UI.VideoPlayer.MainVideoPlayerWindow import *
from GUI.SetupWindow.SetupWindow import *


from GUI.UI.VideoTrackFilterEditWidget.TrackFilterEditDialogBase import TrackFilterEditDialogBase
from GUI.UI.VideoTrackFilterEditWidget.VideoTrackFilterEditDialog import VideoTrackFilterEditDialog

from GUI.Model.Events.PhoDurationEvent_Video import PhoDurationEvent_Video

from GUI.UI.TimelineHeaderWidget.TimelineHeaderWidget import TimelineHeaderWidget

# Track Configs
from GUI.Model.TrackConfigs.AbstractTrackConfigs import TrackConfigurationBase, TrackCache, TrackFilterBase
from GUI.Model.TrackConfigs.VideoTrackConfig import VideoTrackFilter, VideoTrackConfiguration
from GUI.Model.TrackConfigs.PartitionTrackConfig import PartitionTrackFilter, PartitionTrackConfiguration

from GUI.Model.ModelViewContainer import ModelViewContainer

from GUI.UI.TimelineFloatingHeaderWidget.TimelineFloatingHeaderWidget import TimelineFloatingHeaderWidget

from GUI.Model.DataMovieLinkInfo import DataMovieLinkInfo

from GUI.Helpers.DurationRepresentationHelpers import DurationRepresentationMixin, OffsetRepresentationMixin
from GUI.Helpers.MouseTrackingThroughChildrenMixin import MouseTrackingThroughChildrenMixin


from GUI.Model.TrackType import TrackType, TrackStorageArray

from app.filesystem.VideoPreviewThumbnailGeneratingMixin import VideoThumbnail, VideoPreviewThumbnailGenerator
from app.filesystem.FileExporting import FileExportingMixin, FileExportFormat, FileExportOptions



class GlobalTimeAdjustmentOptions(Enum):
        ConstrainGlobalToVideoTimeRange = 1 # adjusts the global start and end times for the timeline to the range of the loaded videos.
        ConstrainVideosShownToGlobal = 2 #  keeps the global the same, and only shows the videos within the global start and end range
        ConstantOffsetFromMostRecentVideo = 3  # adjusts the global to a fixed time prior to the end of the most recent video.


class ViewportScaleAdjustmentOptions(Enum):
        MaintainDesiredViewportZoomFactor = 1 # keeps the self.activeScaleMultiplier the same, and adjusts the self.activeViewportDuration to match upon window resize
        MaintainDesiredViewportDisplayDuration = 2 #  keeps the self.activeViewportDuration the same, and adjusts the self.activeScaleMultiplier to match upon window resize


class VideoTrackGroupSettings:
    def __init__(self, wantsLabeledVideoTrack=False, wantsAnnotationsTrack=True, wantsPartitionTrack=False):
        self.wantsLabeledVideoTrack = wantsLabeledVideoTrack
        self.wantsAnnotationsTrack = wantsAnnotationsTrack
        self.wantsPartitionTrack = wantsPartitionTrack

    # wantsLabeledVideoTrack, wantsAnnotationsTrack, wantsPartitionTrack = self.get_helper_track_preferences()
    def get_helper_track_preferences(self):
        return (self.wantsLabeledVideoTrack, self.wantsAnnotationsTrack, self.wantsPartitionTrack)


class VideoTrackGroup:
    def __init__(self, groupID, videoTrackIndex=None, labeledVideoTrackIndex=None, annotationsTrackIndex=None, partitionsTrackIndex=None):
        self.groupID = groupID
        self.videoTrackIndex = videoTrackIndex
        self.labeledVideoTrackIndex = labeledVideoTrackIndex
        self.annotationsTrackIndex = annotationsTrackIndex
        self.partitionsTrackIndex = partitionsTrackIndex

    def get_group_id(self):
        return self.groupID

    def get_videoTrackIndex(self):
        return self.videoTrackIndex

    def get_labeledVideoTrackIndex(self):
        return self.labeledVideoTrackIndex

    def get_annotationsTrackIndex(self):
        return self.annotationsTrackIndex

    def get_partitionsTrackIndex(self):
        return self.partitionsTrackIndex

    def set_videoTrackIndex(self, newValue):
        self.videoTrackIndex = newValue

    def set_labeledVideoTrackIndex(self, newValue):
        self.labeledVideoTrackIndex = newValue

    def set_annotationsTrackIndex(self, newValue):
        self.annotationsTrackIndex = newValue

    def set_partitionsTrackIndex(self, newValue):
        self.partitionsTrackIndex = newValue






"""
self.activeScaleMultiplier: this multipler determines how many times longer the contents of the scrollable viewport are than the viewport width itself.

"""
class TimelineDrawingWindow(FileExportingMixin, MouseTrackingThroughChildrenMixin, DurationRepresentationMixin, AbstractDatabaseAccessingWindow):
    
    static_VideoTrackTrackID = -1 # The integer ID of the main video track
    
    TraceCursorWidth = 2
    TraceCursorColor = QColor(51, 255, 102)  # Green

    GlobalTimelineConstraintOptions = GlobalTimeAdjustmentOptions.ConstrainGlobalToVideoTimeRange
    # GlobalTimelineConstraintOptions = GlobalTimeAdjustmentOptions.ConstantOffsetFromMostRecentVideo

    # ConstrainToVideoTimeRange = True # If true, adjusts the global start and end times for the timeline to the range of the loaded videos.
    # # If false, only shows the videos within the global start and end range

    # Only used if GlobalTimelineConstraintOptions is .ConstantOffsetFromMostRecentVideo. Specifies the offset prior to the end of the last video which to start the global timeline.
    ConstantOffsetFromMostRecentVideoDuration = timedelta(days=7)

    
    # ViewportAdjustmentMode: Determines how activeScaleMultiplier and activeViewportDuration are set from each other when one is adjusted 
    # ViewportAdjustmentMode = ViewportScaleAdjustmentOptions.MaintainDesiredViewportZoomFactor
    ViewportAdjustmentMode = ViewportScaleAdjustmentOptions.MaintainDesiredViewportDisplayDuration
    # Default viewport width is 1 day
    DefaultViewportDisplayDuration = timedelta(days=4.0)
    # DefaultZoom = 16.0
    DefaultZoom = 8.0

    ZoomDelta = 1.0
    MinZoomLevel = 0.1
    MaxZoomLevel = 2600.0

    DesiredInitialWindowWidth = 1008
    DesiredInitialWindowHeight = 900

    # Signals:
    
    # window_resized: Signal that fires when the window is resized.
    window_resized = QtCore.pyqtSignal()
    activeZoomChanged = pyqtSignal()

    # activeGlobalTimelineTimesChanged(startTime: datetime, endTime: datetime, duration: timedelta)
    activeGlobalTimelineTimesChanged = pyqtSignal(datetime, datetime, timedelta) # Called when the timeline's global displayed start/end times are updated
    activeViewportChanged = pyqtSignal() # Indicates that the active displayed viewport has changed
    
    minimumTimelineTrackWidthChanged = pyqtSignal(float)

    # debug_IncludeTaggedVideoTracks = False
    debug_IncludeEarlyTracks = False

    # debug_desiredVideoTracks = [0, 1, 5, 6, 8, 9]
    # debug_desiredVideoTrackGroupSettings = [VideoTrackGroupSettings(False, True, False), VideoTrackGroupSettings(False, True, False), VideoTrackGroupSettings(False, True, False), VideoTrackGroupSettings(False, True, False), VideoTrackGroupSettings(False, True, False), VideoTrackGroupSettings(False, True, False)]
    
    debug_desiredVideoTracks = [0, 1]
    debug_desiredVideoTrackGroupSettings = [VideoTrackGroupSettings(False, True, True), VideoTrackGroupSettings(False, True, True)]

    # debug_desiredVideoTracks = [5, 6, 8, 9]

    def __init__(self, database_connection, totalStartTime, totalEndTime):
        super(TimelineDrawingWindow, self).__init__(database_connection) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/MainWindow/MainWindow.ui", self) # Load the .ui file

        self.shouldUseTrackHeaders = True

        self.partitionTrackContextsArray = [TrackContextConfig('Behavior'), TrackContextConfig('Unknown')]

        # self.trackConfigurations = []
        self.trackConfigurationsDict = dict()
        # self.trackID_ConfigurationsMap = dict() # a map from trackID to a specific configuration
        self.videoInfoObjects = []

        # Track Options:
        # loadedVideoTrackIndicies: the video tracks to initially add to the track list
        self.loadedVideoTrackIndicies = TimelineDrawingWindow.debug_desiredVideoTracks
        self.loadedVideoHelperTrackPreferences = TimelineDrawingWindow.debug_desiredVideoTrackGroupSettings
        self.trackGroups = []
        self.trackID_to_GroupIndexMap = dict() #Maps a track's trackID to the index of its group in self.trackGroups

        self.trackID_to_TrackWidgetLocatorTuple = dict() #Maps a track's trackID to the a tuple (storageArrayType: TrackStorageArray, storageArrayIndex: Int) that can be used to retreive the widget

        self.viewportAdjustmentMode = TimelineDrawingWindow.ViewportAdjustmentMode        
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)

        # Update the data model, and set up the timeline totalStartTime, totalEndTime, totalDuration from the loaded videos if we're in that enum mode.
        self.reloadModelFromDatabase()
        self.reload_timeline_display_bounds()
        
        if self.viewportAdjustmentMode is ViewportScaleAdjustmentOptions.MaintainDesiredViewportZoomFactor:
            # Compute the correct activeViewportDuration from the activeScaleMultiplier
            self.activeScaleMultiplier = TimelineDrawingWindow.DefaultZoom
            self.activeViewportDuration = TimelineDrawingWindow.compute_desiredViewportDuration_from_activeScaleMultiplier(self.width(), self.totalDuration, self.activeScaleMultiplier)            
            pass
        elif self.viewportAdjustmentMode is ViewportScaleAdjustmentOptions.MaintainDesiredViewportDisplayDuration:
            # Compute the correct activeScaleMultiplier from the activeViewportDuration
            # activeViewportDuration: the desired duration of time to display in the viewport. When adjusted, updates the activeScaleMultiplier (zoom factor)
            self.activeViewportDuration = TimelineDrawingWindow.DefaultViewportDisplayDuration
            self.activeScaleMultiplier = TimelineDrawingWindow.compute_activeScaleMultiplier_from_desiredViewportDuration(self.width(), self.totalDuration, self.activeViewportDuration)
            pass
        else:
            print("FATAL ERROR: Invalid viewportAdjustmentMode!")
            return


        # Reference Manager:
        self.referenceManager = ReferenceMarkerManager(self.totalStartTime, self.totalEndTime, self.width(), 10, parent=self)
        self.referenceManager.used_markers_updated.connect(self.on_reference_line_markers_updated)
        self.referenceManager.wants_extended_data.connect(self.on_request_extended_reference_line_data)
        self.referenceManager.selection_changed.connect(self.on_reference_line_marker_list_selection_changed)

        # self.referenceManager.hoverDatetimeChanged.connect(self.on_reference_indicator_line_hover_changed)
        # self.referenceManager.selectedDatetimeChanged.connect(self.on_reference_indicator_line_selection_changed)


        self.activeZoomChanged.connect(self.referenceManager.on_active_zoom_changed)
        self.activeViewportChanged.connect(self.referenceManager.on_active_viewport_changed)
        self.activeGlobalTimelineTimesChanged.connect(self.referenceManager.on_active_global_timeline_times_changed)
        self.minimumTimelineTrackWidthChanged.connect(self.referenceManager.set_fixed_width)

        # Video Thumbnail Generator:
        self.videoThumbnailGenerator = VideoPreviewThumbnailGenerator([], parent=self)
        self.videoThumbnailGenerator.thumbnailGenerationComplete.connect(self.on_video_thumbnail_generation_complete)

        self.wantsCreateNewVideoPlayerWindowOnClose = False
        # self.pendingCreateVideoPlayerURL = None # self.pendingCreateVideoPlayerURL: holds the URL of the video file that we currently want to load. Used to enable waiting for the previous video player to close before a new one is opened with this URL.
        self.pendingCreateVideoPlayerSelectedItem = None # self.pendingCreateVideoPlayerSelectedItem: holds the URL of the video file that we currently want to load. Used to enable waiting for the previous video player to close before a new one is opened with this URL.

        # Temporary "pending" items that will be set and then cleared once the appropriate action is performed with them
        self.pending_adjust_viewport_start_datetime = None

        self.videoPlayerWindow = None
        self.helpWindow = None
        self.setupWindow = None
        self.videoTreeWindow = None
        self.databaseBrowserUtilityWindow = None
        self.activeVideoTrackConfigEditDialog = None
        self.activeTrackID_ConfigEditingIndex = None
    

        self.minimumVideoTrackHeight = 50
        # self.minimumVideoTrackHeight = 25

        self.minimumEventTrackHeight = 50


        self.initUI()
        self.reload_tracks_from_track_configs()

        # Connect Internal Slots to signals:
        self.window_resized.connect(self.on_window_resized) # A special event that should report when the window is resized.
        self.activeZoomChanged.connect(self.on_active_zoom_changed)
        self.activeViewportChanged.connect(self.on_active_viewport_changed)
        self.activeGlobalTimelineTimesChanged.connect(self.on_active_global_timeline_times_changed)

        self.setMouseTracking(True)
        # self.show() # Show the GUI

        # overlappingVideoEvents = self.mainVideoTrack.find_overlapping_events()
        # for aTuple in overlappingVideoEvents:
        #     print(aTuple)
        # # print(overlappingVideoEvents)

    def get_reference_manager(self):
        return self.referenceManager

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

            self.ui.actionExport_to.triggered.connect(self.on_user_data_export)

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
            self.timelineMasterTrackWidget = QTimeLine(self.totalStartTime, self.totalEndTime, self.totalDuration, masterTimelineDurationSeconds, parent=self)
            self.timelineMasterTrackWidget.setMouseTracking(True)
            self.timelineMasterTrackWidget.hoverChanged.connect(self.handle_timeline_hovered_position_update_event)
            self.timelineMasterTrackWidget.positionChanged.connect(self.handle_timeline_position_update_event)
            self.activeZoomChanged.connect(self.timelineMasterTrackWidget.on_active_zoom_changed)
            self.activeViewportChanged.connect(self.timelineMasterTrackWidget.on_active_viewport_changed)
            self.activeGlobalTimelineTimesChanged.connect(self.timelineMasterTrackWidget.on_active_global_timeline_times_changed)
            self.minimumTimelineTrackWidthChanged.connect(self.timelineMasterTrackWidget.set_fixed_width)
        
            # Video Tracks
            ## TODO: The video tracks must set:
            self.videoFileTrackWidgets = []
            self.eventTrackWidgets = []
            self.trackGroups = []
            self.trackID_to_GroupIndexMap = dict() #Maps a track's trackID to the index of its group in self.trackGroups
            self.trackID_to_TrackWidgetLocatorTuple = dict() #Maps a track's trackID to the a tuple (storageArrayType: TrackStorageArray, storageArrayIndex: Int) that can be used to retreive the widget




            # B00
            currTrackIndex = 0

            # Loop through and create all of the track configs, the track GUI widget objects, etc
            for (index, currTrackBBID) in enumerate(self.loadedVideoTrackIndicies):
                currGroup = VideoTrackGroup(index)

                currTrackConfig = VideoTrackConfiguration(currTrackIndex, "B{0:02}".format(currTrackBBID), "Originals", True, False, [currTrackBBID+1], None, None, None, self)
                self.trackConfigurationsDict[currTrackIndex] = currTrackConfig
                mainVideoTrack = TimelineTrackDrawingWidget_Videos(currTrackConfig, self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
                mainVideoTrack.set_track_title_label('BBID: {0}, originals'.format(currTrackBBID))
                specific_storage_array_index = len(self.videoFileTrackWidgets)
                currGroup.set_videoTrackIndex(specific_storage_array_index)
                self.trackID_to_TrackWidgetLocatorTuple[currTrackIndex] = (currTrackConfig.get_track_storageArray_type(), specific_storage_array_index)
                self.videoFileTrackWidgets.append(mainVideoTrack)
                self.trackID_to_GroupIndexMap[currTrackIndex] = index
                currTrackIndex = currTrackIndex + 1

                currHelperTracksOptions = self.loadedVideoHelperTrackPreferences[index]
                wantsLabeledVideoTrack, wantsAnnotationsTrack, wantsPartitionTrack = currHelperTracksOptions.get_helper_track_preferences()
                # Add the tagged video track for the same box
                if wantsLabeledVideoTrack:
                    currTrackConfig = VideoTrackConfiguration(currTrackIndex, "B{0:02}Labeled".format(currTrackBBID), "Labeled", False, True, [currTrackBBID+1], None, None, None, self)
                    self.trackConfigurationsDict[currTrackIndex] = currTrackConfig
                    self.labeledVideoTrack = TimelineTrackDrawingWidget_Videos(currTrackConfig, self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
                    self.labeledVideoTrack.set_track_title_label('BBID: {0}, labeled'.format(currTrackBBID))
                    specific_storage_array_index = len(self.videoFileTrackWidgets)
                    currGroup.set_labeledVideoTrackIndex(specific_storage_array_index)
                    self.trackID_to_TrackWidgetLocatorTuple[currTrackIndex] = (currTrackConfig.get_track_storageArray_type(), specific_storage_array_index)
                    self.videoFileTrackWidgets.append(self.labeledVideoTrack)
                    self.trackID_to_GroupIndexMap[currTrackIndex] = index
                    currTrackIndex = currTrackIndex + 1

                if wantsAnnotationsTrack:
                    # Annotation Comments track:
                    currTrackConfig = TrackConfigurationBase(currTrackIndex, "A_B{0:02}Notes".format(currTrackBBID), "Notes", TimestampedAnnotation, [currTrackBBID+1], None, None, None, self)
                    self.trackConfigurationsDict[currTrackIndex] = currTrackConfig
                    self.annotationCommentsTrackWidget = TimelineTrackDrawingWidget_AnnotationComments(currTrackConfig, self.totalStartTime, self.totalEndTime, self.database_connection, parent=self, wantsKeyboardEvents=True, wantsMouseEvents=True)
                    specific_storage_array_index = len(self.eventTrackWidgets)
                    currGroup.set_annotationsTrackIndex(specific_storage_array_index)
                    self.trackID_to_TrackWidgetLocatorTuple[currTrackIndex] = (currTrackConfig.get_track_storageArray_type(), specific_storage_array_index)
                    self.eventTrackWidgets.append(self.annotationCommentsTrackWidget)
                    self.trackID_to_GroupIndexMap[currTrackIndex] = index
                    currTrackIndex = currTrackIndex + 1

                if wantsPartitionTrack:
                    # Partition tracks:
                    currPartitionTrackContextObj = self.partitionTrackContextsArray[0]
                    # currTrackConfig = TrackConfigurationBase(currTrackIndex, "P_B{0:02}Parti".format(currTrackBBID), "Parti", CategoricalDurationLabel, [currTrackBBID+1], None, None, None, self)
                    currTrackConfig = PartitionTrackConfiguration(currTrackIndex, "P_B{0:02}Parti".format(currTrackBBID), "Parti", currPartitionTrackContextObj, [currTrackBBID+1], None, None, None, self)
                    self.trackConfigurationsDict[currTrackIndex] = currTrackConfig
                    self.partitionsTrackWidget = TimelineTrackDrawingWidget_Partition(currTrackConfig, self.totalStartTime, self.totalEndTime, self.database_connection, currPartitionTrackContextObj, parent=self)
                    specific_storage_array_index = len(self.eventTrackWidgets)
                    currGroup.set_partitionsTrackIndex(specific_storage_array_index)
                    self.trackID_to_TrackWidgetLocatorTuple[currTrackIndex] = (currTrackConfig.get_track_storageArray_type(), specific_storage_array_index)
                    self.eventTrackWidgets.append(self.partitionsTrackWidget)
                    self.trackID_to_GroupIndexMap[currTrackIndex] = index
                    currTrackIndex = currTrackIndex + 1

                self.trackGroups.append(currGroup)

            # Other Tracks:

            # Build the bottomPanelWidget
            self.extendedTracksContainer = ExtendedTracksContainerWidget(self.totalStartTime, self.totalEndTime, self.totalDuration, masterTimelineDurationSeconds, parent=self)
            self.extendedTracksContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.extendedTracksContainer.setAutoFillBackground(True)
            self.extendedTracksContainer.setMouseTracking(True)
            self.extendedTracksContainer.hoverChanged.connect(self.handle_timeline_hovered_position_update_event)
            self.activeZoomChanged.connect(self.extendedTracksContainer.on_active_zoom_changed)
            self.activeViewportChanged.connect(self.extendedTracksContainer.on_active_viewport_changed)
            self.activeGlobalTimelineTimesChanged.connect(self.extendedTracksContainer.on_active_global_timeline_times_changed)
            self.minimumTimelineTrackWidthChanged.connect(self.extendedTracksContainer.set_fixed_width)

            # bind to self to detect changes in either child
            self.timelineMasterTrackWidget.hoverChanged.connect(self.on_playhead_hover_position_updated)
            self.extendedTracksContainer.hoverChanged.connect(self.on_playhead_hover_position_updated)

            #Layout of Extended Tracks Container Widget
            self.extendedTracksContainerVboxLayout = QVBoxLayout(self)
            self.extendedTracksContainerVboxLayout.addStretch(1)
            self.extendedTracksContainerVboxLayout.addSpacing(2.0)
            self.extendedTracksContainerVboxLayout.setContentsMargins(0,0,0,0)

            self.extendedTracksContainerVboxLayout.addWidget(self.timelineMasterTrackWidget)
            self.timelineMasterTrackWidget.setMinimumSize(minimumWidgetWidth, 50)
            self.timelineMasterTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        def initUI_setupVideoTrackWidget(self, currVideoTrackWidget, currTrackConfigurationIndex):
             # Video track specific setup
            currVideoTrackWidget.selection_changed.connect(self.handle_child_selection_event)
            currVideoTrackWidget.hover_changed.connect(self.handle_child_hover_event)
            currVideoTrackWidget.on_create_marker.connect(self.on_create_playhead_selection)
            
            currVideoTrackWidget.setMouseTracking(True)
            currVideoTrackWidget.shouldDismissSelectionUponMouseButtonRelease = False
            currVideoTrackWidget.itemSelectionMode = ItemSelectionOptions.SingleSelection

            self.minimumTimelineTrackWidthChanged.connect(currVideoTrackWidget.set_fixed_width)

            currHeaderIncludedTrackLayout = QGridLayout(self)
            currHeaderIncludedTrackLayout.setSpacing(0)
            currHeaderIncludedTrackLayout.setContentsMargins(0,0,0,0)
            currHeaderIncludedContainer = QWidget(self)

            currHeaderTrackConfig = self.trackConfigurationsDict[currVideoTrackWidget.get_trackID()]
            currHeaderWidget = TimelineHeaderWidget(currHeaderTrackConfig, parent=self)
            currHeaderWidget.setMinimumSize(50, self.minimumVideoTrackHeight)
            currHeaderWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            currHeaderWidget.toggleCollapsed.connect(self.on_track_header_toggle_collapse_activated)
            currHeaderWidget.showOptions.connect(self.on_track_header_show_options_activated)
            currHeaderWidget.refresh.connect(self.on_track_header_refresh_activated)

            currHeaderWidget.update_labels_dynamically()
            self.videoFileTrackWidgetHeaders[currVideoTrackWidget.get_trackID()] = currHeaderWidget

            # Make the floating label as well
            currFloatingHeader = TimelineFloatingHeaderWidget(currHeaderTrackConfig, parent=self)
            currFloatingHeader.setMinimumSize(25, (self.minimumVideoTrackHeight / 2.0))
            currFloatingHeader.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            currFloatingHeader.update_labels_dynamically()

            currFloatingHeader.findPrevious.connect(self.on_jump_previous_for_track)
            currFloatingHeader.findNext.connect(self.on_jump_next_for_track)
            currFloatingHeader.showOptions.connect(self.on_track_header_show_options_activated)
            currFloatingHeader.refresh.connect(self.on_track_header_refresh_activated)

            self.trackFloatingWidgetHeaders[currVideoTrackWidget.get_trackID()] = currFloatingHeader

            # Set the minimum grid row height
            currFloatingHeaderGridRowID = currTrackConfigurationIndex + 1
            self.timelineViewportLayout.setRowMinimumHeight(currFloatingHeaderGridRowID, self.minimumVideoTrackHeight)


            currHeaderIncludedTrackLayout.addWidget(currVideoTrackWidget, 0, 0, Qt.AlignLeft|Qt.AlignTop)
            currVideoTrackWidget.setMinimumSize(minimumWidgetWidth, self.minimumVideoTrackHeight)
            currVideoTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            currHeaderIncludedTrackLayout.addWidget(currHeaderWidget, 0, 0, Qt.AlignLeft|Qt.AlignTop)

            # Floating header track
            # currHeaderIncludedTrackLayout.addWidget(currFloatingHeader, 0, 0, Qt.AlignHCenter|Qt.AlignTop)


            currHeaderIncludedContainer.setLayout(currHeaderIncludedTrackLayout)

            currHeaderIncludedContainer.setMinimumSize(minimumWidgetWidth, self.minimumVideoTrackHeight)
            currHeaderIncludedContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            self.extendedTracksContainerVboxLayout.addWidget(currHeaderIncludedContainer)

        def initUI_setupEventTrackWidget(self, currWidget, currTrackConfigurationIndex):
            self.minimumTimelineTrackWidthChanged.connect(currWidget.set_fixed_width)

            currHeaderIncludedTrackLayout = QGridLayout(self)
            currHeaderIncludedTrackLayout.setSpacing(0)
            currHeaderIncludedTrackLayout.setContentsMargins(0,0,0,0)
            currHeaderIncludedContainer = QWidget(self)

            currHeaderTrackConfig = self.trackConfigurationsDict[currWidget.get_trackID()]
            
            currHeaderWidget = TimelineHeaderWidget(currHeaderTrackConfig, parent=self)
            currHeaderWidget.setMinimumSize(50, self.minimumEventTrackHeight)
            currHeaderWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            currHeaderWidget.toggleCollapsed.connect(self.on_track_header_toggle_collapse_activated)
            currHeaderWidget.showOptions.connect(self.on_track_header_show_options_activated)
            currHeaderWidget.refresh.connect(self.on_track_header_refresh_activated)

            currHeaderWidget.update_labels_dynamically()
            self.eventTrackWidgetHeaders[currWidget.get_trackID()] = currHeaderWidget

            # Make the floating label as well
            currFloatingHeader = TimelineFloatingHeaderWidget(currHeaderTrackConfig, parent=self)
            currFloatingHeader.setMinimumSize(25, (self.minimumEventTrackHeight / 2.0))
            currFloatingHeader.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            currFloatingHeader.update_labels_dynamically()

            currFloatingHeader.findPrevious.connect(self.on_jump_previous_for_track)
            currFloatingHeader.findNext.connect(self.on_jump_next_for_track)
            currFloatingHeader.showOptions.connect(self.on_track_header_show_options_activated)
            currFloatingHeader.refresh.connect(self.on_track_header_refresh_activated)

            self.trackFloatingWidgetHeaders[currWidget.get_trackID()] = currFloatingHeader

            # Set the minimum grid row height
            currFloatingHeaderGridRowID = currTrackConfigurationIndex + 1
            self.timelineViewportLayout.setRowMinimumHeight(currFloatingHeaderGridRowID, self.minimumEventTrackHeight)

            currHeaderIncludedTrackLayout.addWidget(currWidget, 0, 0, Qt.AlignLeft|Qt.AlignTop)
            currWidget.setMinimumSize(minimumWidgetWidth, self.minimumEventTrackHeight)
            currWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            currHeaderIncludedTrackLayout.addWidget(currHeaderWidget, 0, 0, Qt.AlignLeft|Qt.AlignTop)

            currHeaderIncludedContainer.setLayout(currHeaderIncludedTrackLayout)

            currHeaderIncludedContainer.setMinimumSize(minimumWidgetWidth, self.minimumEventTrackHeight)
            currHeaderIncludedContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            self.extendedTracksContainerVboxLayout.addWidget(currHeaderIncludedContainer)

        def initUI_layout(self):

            currTrackConfigurationIndex = 0

            self.videoFileTrackWidgetHeaders = dict()
            self.trackFloatingWidgetHeaders = dict()
            self.eventTrackWidgetHeaders = dict()

            # Create the layout for the timeline viewport:
            self.timelineViewportLayout = QGridLayout(self)
            self.timelineViewportLayout.setSpacing(0)
            self.timelineViewportLayout.setContentsMargins(0,0,0,0)
            self.timelineViewportContainer = QWidget(self)

            # Add the blank grid row to account for the master track (which should occupy row 0)
            # Set the minimum grid row height
            self.timelineViewportLayout.setRowMinimumHeight(0, 50)

            self.totalTrackCount = len(self.videoFileTrackWidgets) + len(self.eventTrackWidgets)
            self.totalNumGroups = len(self.trackGroups)

            # Loop through the groups to layout the tracks
            for currGroupIndex in range(0, self.totalNumGroups):
                currGroup = self.trackGroups[currGroupIndex]
                if currGroup.get_videoTrackIndex() is not None:
                    currVideoTrackWidget = self.videoFileTrackWidgets[currGroup.get_videoTrackIndex()]
                    # Video track specific setup
                    initUI_setupVideoTrackWidget(self, currVideoTrackWidget, currTrackConfigurationIndex)
                    currTrackConfigurationIndex = currTrackConfigurationIndex + 1

                if currGroup.get_labeledVideoTrackIndex() is not None:
                    currVideoTrackWidget = self.videoFileTrackWidgets[currGroup.get_labeledVideoTrackIndex()]
                    # Video track specific setup
                    initUI_setupVideoTrackWidget(self, currVideoTrackWidget, currTrackConfigurationIndex)
                    currTrackConfigurationIndex = currTrackConfigurationIndex + 1

                if currGroup.get_annotationsTrackIndex() is not None:
                    currWidget = self.eventTrackWidgets[currGroup.get_annotationsTrackIndex()]
                    # Event track specific setup
                    initUI_setupEventTrackWidget(self, currWidget, currTrackConfigurationIndex)
                    currTrackConfigurationIndex = currTrackConfigurationIndex + 1
                    
                if currGroup.get_partitionsTrackIndex() is not None:
                    currWidget = self.eventTrackWidgets[currGroup.get_partitionsTrackIndex()]
                    # Event track specific setup
                    initUI_setupEventTrackWidget(self, currWidget, currTrackConfigurationIndex)
                    currTrackConfigurationIndex = currTrackConfigurationIndex + 1


            # General Layout:
            self.extendedTracksContainer.setLayout(self.extendedTracksContainerVboxLayout)

            self.extendedTracksContainer.setFixedWidth(minimumWidgetWidth)
            ## Scroll Area: should contain only the extendedTracksContainer (not the video container)
            self.timelineScroll = QScrollArea(parent=self)
            self.timelineScroll.setWidget(self.extendedTracksContainer)
            self.timelineScroll.setWidgetResizable(True)
            # self.timelineScroll.setWidgetResizable(False)
            self.timelineScroll.setMouseTracking(True)
            self.timelineScroll.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            self.timelineScroll.horizontalScrollBar().valueChanged.connect(self.on_viewport_slider_changd)
            # self.timelineScroll.setBackgroundRole(QPalette.Dark)
            # self.timelineScroll.setFixedHeight(400)
            # self.timelineScroll.setFixedWidth(self.width())

            # Add the timeline scroll to the layout
            self.timelineViewportLayout.addWidget(self.timelineScroll,0,0,-1,-1) # Set the timeline to span all rows/columns of the layout

            # Add header tracks to self.timelineScroll (the viewport)
            currRowIndex = 1 # the row index starts at 1 to skip the timeline master track
            for (aTrackID, aFloatingHeader) in self.trackFloatingWidgetHeaders.items():
                # self.timelineViewportLayout.addWidget(aFloatingHeader, 0, 0, Qt.AlignHCenter|Qt.AlignTop)
                self.timelineViewportLayout.addWidget(aFloatingHeader, currRowIndex, 0, Qt.AlignRight|Qt.AlignTop)
                currRowIndex = currRowIndex + 1


            # Set the timelineViewportContainer's layout to the timeline viewport layout
            self.timelineViewportContainer.setLayout(self.timelineViewportLayout)
            # timelineViewportContainer.setMinimumSize(minimumWidgetWidth, self.minimumVideoTrackHeight)
            self.timelineViewportContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                

            # Main Vertical Splitter:
            self.verticalSplitter = QSplitter(Qt.Vertical, parent=self)
            self.verticalSplitter.setHandleWidth(8)
            self.verticalSplitter.setMouseTracking(True)
            self.verticalSplitter.addWidget(self.videoPlayerContainer)
            self.verticalSplitter.addWidget(self.timelineViewportContainer)
            # self.verticalSplitter.addWidget(self.timelineScroll)
            self.verticalSplitter.setMouseTracking(True)

            # Size the widgets
            desiredInitialTopVideoPlayerContainerHeight = 0
            desiredInitialTimelineViewportContainerHeight = TimelineDrawingWindow.DesiredInitialWindowHeight - desiredInitialTopVideoPlayerContainerHeight
            self.verticalSplitter.setSizes([desiredInitialTopVideoPlayerContainerHeight, desiredInitialTimelineViewportContainerHeight])

        # Set the initial window size
        self.resize(TimelineDrawingWindow.DesiredInitialWindowWidth, TimelineDrawingWindow.DesiredInitialWindowHeight)
        
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
        self.videoPlayerContainer.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
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

        # The timeline-contents relative X position computed from self.cursorX
        self.timelineCursorX = 0.0
        self.timelineCursorDurationOffset = None
        self.timelineCursorDatetime = None
        #self.cursorTraceRect = QRect(0,0,0,0)

    def reloadModelFromDatabase(self):
        # Context objects for children tracks
        self.contextsDict = self.database_connection.load_contexts_from_database()
        self.subcontexts = self.database_connection.load_subcontexts_from_database()

        try:
            for (index, aPartitionTrackContextInfoObj) in enumerate(self.partitionTrackContextsArray):
                newContext = self.contextsDict[aPartitionTrackContextInfoObj.get_context_name()]
                newSubcontext = newContext.subcontexts[aPartitionTrackContextInfoObj.get_subcontext_index()]
                aPartitionTrackContextInfoObj.update_on_load(newContext, newSubcontext)

        except KeyError as e:
            print("Warning: a requested database key didn't exist in the database! Are the sample contexts/subcontexts successfully added?")
            self.database_connection.initSampleDatabase_ContextsSubcontexts()

            try:
                for (index, aPartitionTrackContextInfoObj) in enumerate(self.partitionTrackContextsArray):
                    newContext = self.contextsDict[aPartitionTrackContextInfoObj.get_context_name()]
                    newSubcontext = newContext.subcontexts[aPartitionTrackContextInfoObj.get_subcontext_index()]
                    aPartitionTrackContextInfoObj.update_on_load(newContext, newSubcontext)

            except KeyError as e:
                print("Error: still failed even after trying to add sample records to database!!!")


        # Video file objects for video tracks
        self.videoFileRecords = self.database_connection.load_video_file_info_from_database()
        self.videoInfoObjects = []
        # Iterate through loaded database records to build videoInfoObjects
        for aVideoFileRecord in self.videoFileRecords:
            aVideoInfoObj = aVideoFileRecord.get_video_info_obj()
            self.videoInfoObjects.append(aVideoInfoObj)

        self.update()

    def update_global_start_end_times(self, totalStartTime, totalEndTime):
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)

        # Emit events
        self.activeGlobalTimelineTimesChanged.emit(self.totalStartTime, self.totalEndTime, self.totalDuration)



    # Required to initialize the viewport to fit the video events
    def reload_timeline_display_bounds(self):
        videoDates = []
        videoEndDates = []

        for (index, videoInfoItem) in enumerate(self.videoInfoObjects):
            videoDates.append(videoInfoItem.startTime)
            videoEndDates.append(videoInfoItem.endTime)

        self.videoDates = np.array(videoDates)
        self.videoEndDates = np.array(videoEndDates)

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

    def reload_tracks_from_track_configs(self):
        self.reload_videos_from_track_configs()
        self.reload_events_from_track_configs()

    # Reloads the video records from the current track configs
    def reload_videos_from_track_configs(self):
        if not self.shouldUseTrackHeaders:
            print("Warning: Track headers-based configs are disabled!")
            return

        # Loop through the videoFileTrackWidgets and add them
        for i in range(0, len(self.videoFileTrackWidgets)):
            currVideoTrackWidget = self.videoFileTrackWidgets[i]
            currVideoTrackHeader = self.videoFileTrackWidgetHeaders[currVideoTrackWidget.trackID]
            currVideoTrackConfig = currVideoTrackHeader.get_config()

            currVideoTrackConfig.reload(self.database_connection.get_session(), currVideoTrackWidget)

    def reload_events_from_track_configs(self):
        if not self.shouldUseTrackHeaders:
            print("Warning: Track headers-based configs are disabled!")
            return

        # Loop through the videoFileTrackWidgets and add them
        for i in range(0, len(self.eventTrackWidgets)):
            currTrackWidget = self.eventTrackWidgets[i]
            currTrackHeader = self.eventTrackWidgetHeaders[currTrackWidget.trackID]
            currTrackConfig = currTrackHeader.get_config()
            currTrackConfig.reload(self.database_connection.get_session(), currTrackWidget)

        

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

    # Want the offset into the timeline, so it should be self.minimumTimelineWidth * percent_offset.
    # When I resize the window, the viewport gets larger but the minimumTrackWidth should be unchanged. (as it depends only on the scale)
    #   That's not quite right, as it's set initially by the window's initial width isn't it?
        # The minimum_track_width is self.activeScaleMultiplier * the current window width, meaning it DOES change when the window is resized.
        # I assume minimum track width isn't being updated when the window is resized.

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

    # Computes the position in the scroll view's contents (the timeline track offset position) from the viewport's/window's viewport_x_offset
    def viewport_offset_to_contents_offset(self, viewport_x_offset):
        # print("TimelineDrawingWindow.viewport_offset_to_contents_offset(viewport_x_offset: {0})...".format(str(viewport_x_offset)))
        contentWidget = self.timelineScroll.widget()
        contentWidgetRelativePoint = contentWidget.mapFromParent(QPoint(viewport_x_offset, 0))
        return contentWidgetRelativePoint.x()



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
        
        # track_offset_x = self.percent_offset_to_track_offset(self.get_viewport_percent_scrolled())
        # duration_offset = self.offset_to_duration(self.cursorX)
        # datetime = self.offset_to_datetime(self.cursorX)

        # Get scrollview x_offset from window x_offset
        self.timelineCursorX = self.viewport_offset_to_contents_offset(self.cursorX)
        self.timelineCursorDurationOffset = self.offset_to_duration(self.timelineCursorX)
        self.timelineCursorDatetime = self.offset_to_datetime(self.timelineCursorX)

        text = "window x: {0}, contents_x: {1},  duration: {2}, datetime: {3}".format(self.cursorX, self.timelineCursorX, self.timelineCursorDurationOffset, str(datetime))
        # Call the on_mouse_moved handler for the video track which will update its .hovered_object property, which is then read and used for relative offsets

        for (anIndex, aTimelineVideoTrack) in enumerate(self.videoFileTrackWidgets):
            potentially_hovered_child_object = aTimelineVideoTrack.hovered_object
            if potentially_hovered_child_object:
                relative_duration_offset = potentially_hovered_child_object.compute_relative_offset_duration(self.timelineCursorDatetime)
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
        ## Detect modifier keys being held down to modify scroll action.
        """
        Shift Held down: Triple the timeline x-offset speed.
        Ctrl Held down: Zoom in and out instead of modifying the timeline x-offset

        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            # Speed-scroll (3x faster)
            # print('Shift+Scroll')
            dy = 3 * dy
            hsb.setSliderPosition(hsb.sliderPosition()+dy)

        elif modifiers == QtCore.Qt.ControlModifier:
            # print('Control+Scroll')
            # Zoom in/out
            # TODO: Scroll should zoom in/out instead of scroll horizontally. Should zoom centered on the mouse cursor location.
            # zoomInFactor = 1.25
            # zoomOutFactor = 1 / zoomInFactor

            # Set Anchors
            # self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
            # self.setResizeAnchor(QtGui.QGraphicsView.NoAnchor)

            # Save the scene pos
            # oldPos = self.mapToScene(event.pos())
            oldPos = event.pos()

            # Capture the view offset:
            originalViewportDateOffset = self.get_viewport_active_start_time()


            # Zoom
            if event.angleDelta().y() > 0:
                # zoomFactor = zoomInFactor
                print("Zooming in.")
                self.on_zoom_in()
            else:
                print("Zooming out.")
                # zoomFactor = zoomOutFactor
                self.on_zoom_out()
            
            # self.scale(zoomFactor, zoomFactor)
            
            # Get the new position
            # newPos = self.mapToScene(event.pos())
            newPos = event.pos()

            # Move scene to old position
            delta = newPos - oldPos
            # self.translate(delta.x(), delta.y())

            # time.delay(2)

            # Jump to the original offset:
            self.sync_active_viewport_start_to_datetime(originalViewportDateOffset)




        elif modifiers == (QtCore.Qt.ControlModifier |
                           QtCore.Qt.ShiftModifier):
            # Scroll
            # print('Control+Shift+Scroll')
            hsb.setSliderPosition(hsb.sliderPosition()+dy)
        else:
            # Scroll
            # print('Scroll (no modifiers)')
            hsb.setSliderPosition(hsb.sliderPosition()+dy)




    ## Zoom in/default/out events
    def get_minimum_track_width(self):
        return  (self.width() * self.activeScaleMultiplier)

    # Sets the self.activeScaleMultipler based on the desiredMinimumWidth
    # returns the new active scale multiplier
    def set_minimum_track_width(self, desiredMinimumWidth):
        newActiveScaleMultiplier = desiredMinimumWidth / self.width()
        self.set_new_active_scale_multiplier(newActiveScaleMultiplier)
        return self.activeScaleMultiplier

    def get_viewport_width(self):
        return self.timelineScroll.width()

    # Get scale from length. Only used for ReferenceManager
    def getScale(self):
        return float(self.totalDuration.total_seconds())/float(self.get_minimum_track_width())


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
        self.set_new_desired_viewport_duration(desiredDuration)
        return self.activeScaleMultiplier

    """ STATICMETHOD: compute_activeScaleMultiplier_from_desiredViewportDuration(currentViewportWidth, totalTimelineDuration, desiredViewportDisplayDuration)
    Given: a desired duration to display in the viewport
    Return: the correct activeScaleMultiplier (zoom factor) that would need to be set at the current window width.
    Invalidated:    1. when window width is updated
                    2. total duration changes.
    """
    @staticmethod
    def compute_activeScaleMultiplier_from_desiredViewportDuration(currentViewportWidth, totalTimelineDuration, desiredViewportDisplayDuration):
        desiredPercent = desiredViewportDisplayDuration / totalTimelineDuration
        desiredMinimumWidth = (float(currentViewportWidth) / float(desiredPercent))
        newActiveScaleMultiplier = desiredMinimumWidth / float(currentViewportWidth)
        return newActiveScaleMultiplier

    """ STATICMETHOD: compute_desiredViewportDuration_from_activeScaleMultiplier(currentViewportWidth, totalTimelineDuration, desiredActiveScaleMultiplier)
    Given: a desired active scale multiplier (zoom factor) for the viewport
    Return: the correct desiredViewportDuration that would need to be set at the current window width.
    Invalidated:    1. when window width is updated
                    2. total duration changes.
    """
    @staticmethod
    def compute_desiredViewportDuration_from_activeScaleMultiplier(currentViewportWidth, totalTimelineDuration, desiredActiveScaleMultiplier):
        desiredMinimumWidth = desiredActiveScaleMultiplier * float(currentViewportWidth)
        desiredPercent = float(currentViewportWidth) / float(desiredMinimumWidth)
        newActiveViewportDuration = desiredPercent * totalTimelineDuration
        return newActiveViewportDuration



    """ compute_current_activeScaleMultiplier_from_desiredViewportDuration(desiredViewportDisplayDuration)
    Given: a desired duration to display in the viewport
    Return: the correct activeScaleMultiplier (zoom factor) that would need to be set at the current window width.
    Invalidated:    1. when window width is updated
                    2. total duration changes.
    """
    def compute_current_activeScaleMultiplier_from_desiredViewportDuration(self, desiredViewportDisplayDuration):
        return TimelineDrawingWindow.compute_activeScaleMultiplier_from_desiredViewportDuration(self.get_viewport_width(), self.totalDuration, desiredViewportDisplayDuration)

    """ compute_current_desiredViewportDuration_from_activeScaleMultiplier(desiredActiveScaleMultiplier)
    Given: a desired active scale multiplier (zoom factor) for the viewport
    Return: the correct desiredViewportDuration that would need to be set at the current window width.
    Invalidated:    1. when window width is updated
                    2. total duration changes.
    """
    def compute_current_desiredViewportDuration_from_activeScaleMultiplier(self, desiredActiveScaleMultiplier):
        return TimelineDrawingWindow.compute_desiredViewportDuration_from_activeScaleMultiplier(self.get_viewport_width(), self.totalDuration, desiredActiveScaleMultiplier)


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
    ## TODO: Implement
    def preserve_cursor_offset_on_zoom(self):
        # Get cursor position's datetime
        
        pass

    def restore_cursor_offset_after_zoom(self):
        pass

    def on_zoom_in(self):
        # self.pending_adjust_viewport_start_datetime = self.get_viewport_active_start_time()
        newActiveScaleMultiplier = min(TimelineDrawingWindow.MaxZoomLevel, (self.activeScaleMultiplier + TimelineDrawingWindow.ZoomDelta))
        self.set_new_active_scale_multiplier(newActiveScaleMultiplier)

    def on_zoom_home(self):
        # current_viewport_start_time = self.get_viewport_active_start_time()
        newActiveScaleMultiplier = TimelineDrawingWindow.DefaultZoom
        self.set_new_active_scale_multiplier(newActiveScaleMultiplier)
        # self.sync_active_viewport_start_to_datetime(current_viewport_start_time) # Use the saved start time to re-align the viewport's left edge

    def on_zoom_current_video(self):
        # on_zoom_current_video(): zooms the viewport to fit the current video
        print("on_zoom_current_video()")
        # Gets the current video

        selected_video_event_objects_flat_array, outEventsDict = self.get_selected_video_items()
        if (len(selected_video_event_objects_flat_array) <= 0):
            print("WARNING: no selected videos!")
            return
        else:
            # Get the first selected video item
            selected_video_event_tuple = selected_video_event_objects_flat_array[0]
            selected_video_event_obj = selected_video_event_tuple[1] # get the event item from the second element of the tuple

            if selected_video_event_obj is None:
                print("ERROR: invalid video selected!")
                return
            
            newViewportStartTime = selected_video_event_obj.startTime
            newViewportEndTime = selected_video_event_obj.endTime
            newViewportDuration = selected_video_event_obj.computeDuration()

            if newViewportDuration is None:
                print("ERROR: selected video has a None duration!")
                return
            else:
                self.set_viewport_to_range(newViewportStartTime, newViewportEndTime)

            return

    def on_zoom_out(self):
        # Save the datetime represented by the viewport's left edge so that it can be re-aligned after zoom is performed.
        # current_viewport_start_time = self.get_viewport_active_start_time()
        newActiveScaleMultiplier = max(TimelineDrawingWindow.MinZoomLevel, (self.activeScaleMultiplier - TimelineDrawingWindow.ZoomDelta))
        self.set_new_active_scale_multiplier(newActiveScaleMultiplier)
        # self.sync_active_viewport_start_to_datetime(current_viewport_start_time) # Use the saved start time to re-align the viewport's left edge
        
    def on_finish_editing_zoom_custom(self):
        # print("on_finish_editing_zoom_custom()")
        # Save the datetime represented by the viewport's left edge so that it can be re-aligned after zoom is performed.
        # current_viewport_start_time = self.get_viewport_active_start_time()
        double_newZoom = self.ui.doubleSpinBox_currentZoom.value()
        # print("new_zoom: {0}".format(double_newZoom))
        newActiveScaleMultiplier = double_newZoom
        self.set_new_active_scale_multiplier(newActiveScaleMultiplier)
        # self.sync_active_viewport_start_to_datetime(current_viewport_start_time) # Use the saved start time to re-align the viewport's left edge

    def get_viewport_offset_display_string(self):
        outString = str("{0:.6f} | ".format(round(self.get_viewport_percent_scrolled(),6)))

        viewport_start_time = self.get_viewport_active_start_time()
        viewport_start_time_string = viewport_start_time.strftime("X%m/X%d X%I:%m%p").replace('X0', 'X').replace('X', '')
        outString = outString + viewport_start_time_string

        return outString

    def refreshUI_viewport_zoom_controls(self):
        self.ui.doubleSpinBox_currentZoom.blockSignals(True)
        self.ui.doubleSpinBox_currentZoom.setValue(self.activeScaleMultiplier)
        self.ui.doubleSpinBox_currentZoom.blockSignals(False)
        self.ui.lblActiveTotalTimelineDuration.setText(str(self.totalDuration))

    def refreshUI_viewport_info_labels(self):
        self.ui.lblActiveViewportDuration.setText(str(self.get_active_viewport_duration()))
        self.ui.lblActiveViewportOffsetAbsolute.setText(self.get_viewport_offset_display_string())

    def resize_children_on_zoom(self):
        newMinWidth = self.get_minimum_track_width()
        self.extendedTracksContainer.setFixedWidth(newMinWidth)
        self.update()

    ## Navigation:
    
    # Returns the current perent scrolled the viewport is through the entire timeline.
    def get_viewport_percent_scrolled(self):
        # TODO: check that this is correct. I think it is.
        return (float(self.timelineScroll.horizontalScrollBar().value()) / (float(self.timelineScroll.horizontalScrollBar().maximum()) - float(self.timelineScroll.horizontalScrollBar().minimum())))


    # Scrolls the viewport to the desired percent_scrolled of entire timeline.
    def set_viewport_percent_scrolled(self, percent_scrolled):
        scrollbar_scroll_relative_offset = (float(percent_scrolled) * (float(self.timelineScroll.horizontalScrollBar().maximum()) - float(self.timelineScroll.horizontalScrollBar().minimum())))
        scrollbar_offset = scrollbar_scroll_relative_offset + float(self.timelineScroll.horizontalScrollBar().minimum())
        self.timelineScroll.horizontalScrollBar().setValue(scrollbar_offset)

    # Moves and sizes the current viewport's position such that it's start position is aligned with a specific start_time and its end position is aligned with a specific end_time. This also adjusts the zoom!
    def set_viewport_to_range(self, start_time, end_time):
        newViewportDuration = end_time - start_time
        if newViewportDuration is None:
            print("selected range has a None duration!")
            return False
        
        # Compute appropriate zoom.
        newZoom = self.set_active_viewport_duration(newViewportDuration)
        # self.on_active_zoom_changed()
        return self.sync_active_viewport_start_to_datetime(start_time)

    # Gets the start datetime aligned with the left edge of the viewport
    def get_viewport_active_start_time(self):
        track_offset_x = self.percent_offset_to_track_offset(self.get_viewport_percent_scrolled())
        offset_datetime = self.offset_to_datetime(track_offset_x)
        return offset_datetime

    # Moves the current viewport's position such that it's start position is aligned with a specific start_time
    def sync_active_viewport_start_to_datetime(self, start_time):
        # get the viewport's end time
        end_time = start_time + self.get_active_viewport_duration()
        return self.sync_active_viewport_end_to_datetime(end_time)

    # Moves the current viewport's position such that it's end position is aligned with a specific end_time
    def sync_active_viewport_end_to_datetime(self, end_time):
        safe_end_time = end_time
        if end_time > self.totalEndTime:
            print("Warning: end_time > self.totalEndTime!, setting end_time to self.totalEndTime")
            safe_end_time = self.totalEndTime
            # return False

         # Compute appropriate offset:
        found_x_offset = self.datetime_to_offset(safe_end_time)
        # print("TimelineDrawingWindow.sync_active_viewport_end_to_datetime(endTime: {0}): found_x_offset: {1}".format(str(safe_end_time), str(found_x_offset)))
        self.timelineScroll.ensureVisible(found_x_offset, 0, 0, 0)

        # Shouldn't be needed because it triggers self.on_viewport_slider_changd(...)
        # Not calling self.on_active_zoom_changed() results in the floating headers not redrawing until the mouse moves over them for some reason...
        self.on_active_zoom_changed()
        return True
        
        
    ## These functions use the dictionary and array objects built up during initialization to retrieve tracks, configs, and headers by a given trackID.
    # find the track widget with the corresponding trackID
    def get_track_with_trackID(self, trackID):
        currLocatorTuple = self.trackID_to_TrackWidgetLocatorTuple[trackID]
        track_storage_array_type = currLocatorTuple[0]
        track_stroage_array_index = currLocatorTuple[1]
        found_track_widget = None
        if track_storage_array_type == TrackStorageArray.Video:
            found_track_widget = self.videoFileTrackWidgets[track_stroage_array_index]
            pass
        elif track_storage_array_type == TrackStorageArray.Event:
            found_track_widget = self.eventTrackWidgets[track_stroage_array_index]
            pass
        else:
            print("UNIMPLEMENTED ERROR: get_track_with_trackID({0})".format(str(trackID)))
            return None
        
        return found_track_widget

    # find the track header widget with the corresponding trackID
    def get_track_header_with_trackID(self, trackID):
        currLocatorTuple = self.trackID_to_TrackWidgetLocatorTuple[trackID]
        track_storage_array_type = currLocatorTuple[0]
        track_stroage_array_index = currLocatorTuple[1]
        found_obj = None
        if track_storage_array_type == TrackStorageArray.Video:
            found_obj = self.videoFileTrackWidgetHeaders[trackID]
            pass
        elif track_storage_array_type == TrackStorageArray.Event:
            found_obj = self.eventTrackWidgetHeaders[trackID]
            pass
        else:
            print("UNIMPLEMENTED ERROR: get_track_header_with_trackID({0})".format(str(trackID)))
            return None
        
        return found_obj

    # find the track header widget with the corresponding trackID
    def get_track_floating_header_with_trackID(self, trackID):
        return self.trackFloatingWidgetHeaders[trackID] # The floating headers are easy, as they're all in the same dictionary for both Video and Event tracks. Implemented just for consistency with self.get_track_header_with_trackID(trackID).




    ## Timeline Navigation:
    def on_jump_to_start(self):
        print("on_jump_to_start()")
        self.timelineScroll.horizontalScrollBar().setValue(self.timelineScroll.horizontalScrollBar().minimum())
        self.on_active_zoom_changed()
        
    @pyqtSlot(int)
    def on_jump_previous_for_track(self, trackID):
        # Jump to the previous available duration event in the track with the specified trackID
        print("on_jump_previous_for_track(trackID: {0})".format(str(trackID)))
        currFoundTrack = self.get_track_with_trackID(trackID)

        offset_datetime = self.get_viewport_active_start_time()
        # next_video_tuple: (index, videoObj) pair
        prev_event_tuple = currFoundTrack.find_previous_event(offset_datetime)
        if prev_event_tuple is None:
            print("prev_event_tuple is none!")
            return
        else:
            print("prev_event_tuple is {0}".format(prev_event_tuple[0]))

        found_start_date = prev_event_tuple[1].startTime
        self.sync_active_viewport_start_to_datetime(found_start_date)
        return

    def on_jump_previous(self):
        print("on_jump_previous()")
        # Jump to the previous available video in the video track
        # TODO: could highlight the video that's being jumped to.
        offset_datetime = self.get_viewport_active_start_time()
        # next_video_tuple: (index, videoObj) pair
        prev_video_tuple = self.videoFileTrackWidgets[0].find_previous_event(offset_datetime)
        if prev_video_tuple is None:
            print("prev_video_tuple is none!")
            return
        else:
            print("prev_video_tuple is {0}".format(prev_video_tuple[0]))

        found_start_date = prev_video_tuple[1].startTime
        self.sync_active_viewport_start_to_datetime(found_start_date)
        return

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

    @pyqtSlot(int)
    def on_jump_next_for_track(self, trackID):
        # Jump to the next available duration event in the track with the specified trackID
        print("on_jump_next_for_track(trackID: {0})".format(str(trackID)))
    
        # currTrackConfig = self.trackConfigurationsDict[trackID]
        # currGroupIndex = self.trackID_to_GroupIndexMap[trackID]
        # currGroup = self.trackGroups[currGroupIndex]
        # # currTrackConfig = currDestTrackHeader.get_config()

        # currTrackObj = None

        # if (currTrackConfig.get_track_type() == TrackType.Video):
        #     # video track
        #     currTrackObj = 
        # elif (currTrackConfig.get_track_type() == TrackType.Annotation):
        #     # annotation track
        #     pass
        # elif (currTrackConfig.get_track_type() == TrackType.Partition):
        #     # partition track
        #     pass
        # else:

        currFoundTrack = self.get_track_with_trackID(trackID)

        offset_datetime = self.get_viewport_active_start_time()
        # next_event_tuple: (index, eventDurationObj) pair
        next_event_tuple = currFoundTrack.find_next_event(offset_datetime)
        if next_event_tuple is None:
            print("next_event_tuple is none!")
            return
        else:
            print("next_event_tuple is {0}".format(next_event_tuple[0]))

        found_start_date = next_event_tuple[1].startTime
        self.sync_active_viewport_start_to_datetime(found_start_date)
        return

    def on_jump_next(self):
        # Jump to the next available video in the video track
        # TODO: could highlight the video that's being jumped to.
        print("on_jump_next()")
        offset_datetime = self.get_viewport_active_start_time()
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
            self.videoPlayerWindow.close_signal.connect(self.on_video_player_window_closed)
            self.videoPlayerWindow.show()

    def try_set_video_player_window_url(self, url):
        #TODO: temp: set the videoPlayerWindow to None to ensure that a new one is created. Note that setting it to None doesn't actually close the old one.
        # self.videoPlayerWindow = None
        
        if (not (self.videoPlayerWindow is None)):
            # print("Using existing Video Player Window...")
            print("Closing existing Video Player Window...")
            self.videoPlayerWindow.close()
            self.wantsCreateNewVideoPlayerWindowOnClose = True
            self.pendingCreateVideoPlayerURL = url

            # Close the previous window and wait for it to be done closing before creating a new one.

            # self.videoPlayerWindow.movieLink = None # Disable the movieLink
            # self.videoPlayerWindow.set_timestamp_filename(r"C:\Users\halechr\repo\looper\testdata\NewTimestamps.tmsp")
            # self.videoPlayerWindow.set_video_filename(url)

            # self.videoPlayerWindow.show()
        else:
            # Create a new videoPlayerWindow window
            print("Creating new Video Player Window...")
            try:
                self.videoPlayerWindow = MainVideoPlayerWindow(parent=self)
                self.videoPlayerWindow.close_signal.connect(self.on_video_player_window_closed)
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

            self.videoPlayerWindow.movieLink = DataMovieLinkInfo(self.pendingCreateVideoPlayerSelectedItem, self.videoPlayerWindow, self, parent=self)
            
            # if self.wantsCreateNewVideoPlayerWindowOnClose:
            # Set the property false after the window has been created
            self.wantsCreateNewVideoPlayerWindowOnClose = False
            self.pendingCreateVideoPlayerSelectedItem = None
            self.pendingCreateVideoPlayerURL = None


            return True


    # Called when the video player window closes.
    @pyqtSlot()
    def on_video_player_window_closed(self):
        """ Cleanup the popup widget here """
        print("TimelineDrawingWindow.on_video_player_window_closed()...")
        print("Popup closed.")

        # Deselect the video in the timeline:
        for aVideoTrackIndex in range(0, len(self.videoFileTrackWidgets)):
            currVideoTrackWidget = self.videoFileTrackWidgets[aVideoTrackIndex]
            currVideoTrackWidget.clear_now_playing() 
            currVideoTrackWidget.deselect_all()
            currVideoTrackWidget.update()

        # Remove the red playback line:
        self.timelineMasterTrackWidget.blockSignals(True)
        self.extendedTracksContainer.blockSignals(True)

        self.get_reference_manager().on_update_indicator_video_playback(None)
        self.timelineMasterTrackWidget.on_update_video_line(None)
        self.extendedTracksContainer.on_update_video_line(None)

        self.timelineMasterTrackWidget.update()
        self.extendedTracksContainer.update()
        
        self.extendedTracksContainer.blockSignals(False)
        self.timelineMasterTrackWidget.blockSignals(False)

        self.videoPlayerWindow = None

        if self.wantsCreateNewVideoPlayerWindowOnClose:
            # open the pending URL in a new video player window after the previous one was successfully closed.
            self.try_set_video_player_window_url(self.pendingCreateVideoPlayerURL)



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



    # Selection and such:
    def get_selected_video_items(self):
        outEventsFlatArray = [] # a flattened array of (trackID: int, eventsList: PhoDurationEvent) tuples
        outEventsDict = dict() # a [trackID: int, eventsList: list] dictionary

        for aVideoTrack in self.videoFileTrackWidgets:
            currTrackID = aVideoTrack.get_trackID()
            # currSelectedVideoEventIndicies = aVideoTrack.get_selected_event_indicies()
            currSelectedVideoEventObjects = aVideoTrack.get_selected_duration_objects()
            outEventsDict[currTrackID] = currSelectedVideoEventObjects

            for aVideoEventObj in currSelectedVideoEventObjects:
                outEventsFlatArray.append((currTrackID, aVideoEventObj))
        
        return (outEventsFlatArray, outEventsDict)


    # @pyqtSlot(int, int)
    # Occurs when the user selects an object (durationObject) in the child video track with the mouse
    """
    # Selecting a non-video track event shouldn't deselect the video. Likewise, selecting a new video shouldn't deselect comments or partitions (I don't think).
    """
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

            for index in range(0, len(self.videoFileTrackWidgets)):
                currVideoTrackWidget = self.videoFileTrackWidgets[index]
                # currVideoTrackWidget.set_active_filter(self.totalStartTime, self.totalEndTime)
                currVideoTrackWidget.deselect_all()
                currVideoTrackWidget.update()
            
            
        else:
            # Get the selected video object
            # currHoveredObject = self.mainVideoTrack.hovered_object

            # currSelectedObjectIndex = self.mainVideoTrack.selected_duration_object_indicies[0]
            currSelectedObjectIndex = trackObjectIndex

            # Get the track from its trackID. It may not be a video track.
            currActiveTrack = self.get_track_with_trackID(trackIndex)
            # currActiveTrack = self.videoFileTrackWidgets[trackIndex]
            currSelectedObject = currActiveTrack.durationObjects[trackObjectIndex]
            
            # Deselect any other video timelines
            for index in range(0, len(self.videoFileTrackWidgets)):
                aVideoTrackObj = self.videoFileTrackWidgets[index]
                aVideoTrackID = aVideoTrackObj.get_trackID()
                if (aVideoTrackID == trackIndex):
                    # Skip the active track
                    continue
                else:
                    aVideoTrackObj.deselect_all()
                    aVideoTrackObj.update()



            if currSelectedObject is not None:
                selected_video_path = currSelectedObject.get_video_url()
                # print(selected_video_path)
                
                if currSelectedObject.is_video_url_accessible():
                    currActiveTrack.set_now_playing(trackObjectIndex)
                    self.pendingCreateVideoPlayerSelectedItem = currSelectedObject
                    self.try_set_video_player_window_url(str(selected_video_path))
                    
                else:
                    self.pendingCreateVideoPlayerSelectedItem = None
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
    
        for i in range(0, len(self.videoFileTrackWidgets)):
            currWidget = self.videoFileTrackWidgets[i]
            currWidget.update()

        for i in range(0, len(self.eventTrackWidgets)):
            currWidget = self.eventTrackWidgets[i]
            currWidget.update()

    # Called to update the red video playback indicator line
    @pyqtSlot(float)
    def on_video_playback_position_updated(self, timeline_percent_offset):
        # print("on_video_playback_position_updated({0})".format(str(timeline_percent_offset)))
        timeline_x_offset = self.percent_offset_to_track_offset(timeline_percent_offset)

        self.timelineMasterTrackWidget.blockSignals(True)
        self.extendedTracksContainer.blockSignals(True)

        curr_datetime = self.offset_to_datetime(timeline_x_offset)
        self.get_reference_manager().on_update_indicator_video_playback(curr_datetime)

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

        curr_datetime = self.offset_to_datetime(x)
        self.get_reference_manager().on_update_indicator_hover(curr_datetime)
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


    ## Playhead Operations:
    @pyqtSlot(datetime)
    def on_create_playhead_selection(self, desired_datetime):
        # Tries to create a reference marker at the desired_datetime
        print("TimelineDrawingWindow.on_create_playhead_selection({0})".format(str(desired_datetime)))
        # x_offset = self.datetime_to_offset(desired_datetime)

        percent_offset = self.datetime_to_percent(desired_datetime)
        x_offset = self.percent_offset_to_track_offset(percent_offset)

        print("\nDEBUG: TimelineDrawingWindow.on_create_playhead_selection({0}): x-offset: {1}".format(str(desired_datetime), str(x_offset)))
        self.timelineMasterTrackWidget.blockSignals(True)
        self.extendedTracksContainer.blockSignals(True)

        # Update the reference manager
        # self.referenceManager.update_next_unused_marker(x_offset)
        self.referenceManager.update_next_unused_marker(desired_datetime, self.get_minimum_track_width())

        self.timelineMasterTrackWidget.update()
        self.extendedTracksContainer.update()

        self.extendedTracksContainer.blockSignals(False)
        self.timelineMasterTrackWidget.blockSignals(False)

    @pyqtSlot(list)
    def on_request_extended_reference_line_data(self, referenceLineList):
        print("TimelineDrawingWindow.request_extended_reference_line_data(...)")
        # on_request_extended_reference_line_data(,,,): called by ReferenceMarkerManager to get the datetime information to display in the list
        additional_data = []
        for aListItem in referenceLineList:
            curr_view = aListItem.get_view()
            curr_x = curr_view.get_x_offset_position()
            curr_datetime = self.offset_to_datetime(curr_x)
            additional_data.append(curr_datetime)

        self.referenceManager.update_marker_metadata(additional_data)



    @pyqtSlot(list)
    def on_reference_line_markers_updated(self, referenceLineList):
        print("TimelineDrawingWindow.on_reference_line_markers_updated(...)")
        additional_data = []
        for aListItem in referenceLineList:
            curr_view = aListItem.get_view()
            curr_x = curr_view.get_x_offset_position()
            curr_datetime = self.offset_to_datetime(curr_x)
            additional_data.append(curr_datetime)

        print(additional_data)
        #  self.referenceManager.

        
    # @pyqtSlot(list, int)
    # def on_reference_line_marker_list_selection_changed(self, referenceLineList, selected_index):
    #     print("TimelineDrawingWindow.on_reference_line_marker_list_selection_changed(referenceLineList, selected_index: {0})".format(str(selected_index)))
    #      # on_reference_line_marker_list_selection_changed(,,,): called by ReferenceMarkerManager to get the datetime information to display in the list

    @pyqtSlot(list, list)
    def on_reference_line_marker_list_selection_changed(self, referenceLineList, selected_indicies):
        print("TimelineDrawingWindow.on_reference_line_marker_list_selection_changed(referenceLineList, selected_indicies: {0})".format(str(selected_indicies)))
         # on_reference_line_marker_list_selection_changed(,,,): called by ReferenceMarkerManager to get the datetime information to display in the list


    # try_get_reference_lines(): Tries to get all the reference items and their metadata
    def try_get_reference_lines(self):
        curr_markers = self.referenceManager.get_used_markers()
        # Build the metadata
        output_data = []
        for aListItem in curr_markers:
            # combine the datetime and the list item as a tuple
            output_data.append(aListItem)

        # Assuming there's two valid markers, return them in order
        output_data.sort(key = lambda combined_entry: combined_entry.get_record().time)


        # for aListItem in curr_markers:
        #     curr_view = aListItem.get_view()
        #     curr_x = curr_view.get_x_offset_position()
        #     curr_datetime = self.offset_to_datetime(curr_x)
        #     # combine the datetime and the list item as a tuple
        #     output_data.append(curr_datetime, aListItem)

        # # Assuming there's two valid markers, return them in order
        # output_data.sort(key = lambda mark_tuple: mark_tuple[0])

        return output_data


    # try_get_selected_reference_lines(): Tries to get the currently selected reference items
    def try_get_selected_reference_lines(self):
        curr_reference_line_data = self.try_get_reference_lines()
        # Get selected markers from here
        active_window = self.referenceManager.activeMarkersWindow
        if (active_window is None):
            print("ERROR: no active window! Can't get selection!")
            return

        curr_active_inidices = active_window.get_selected_item_indicies()

        # Get the active items from the indicies
        curr_complete_active_items = []
        for anIndex in curr_active_inidices:
            curr_complete_active_items.append(curr_reference_line_data[anIndex])

        return curr_complete_active_items
    


    

    # try_create_comment_from_selected_reference_lines(): tries to create a new annotation comment from the selected reference marks
    @pyqtSlot()
    def try_create_comment_from_selected_reference_lines(self):
        print("try_create_comment_from_selected_reference_lines(...)")
        selected_ref_lines = self.try_get_selected_reference_lines()
        if len(selected_ref_lines)<2:
            print("Couldn't get two selected reference items!!")
            return
        else:
            first_item = selected_ref_lines[0]
            second_item = selected_ref_lines[1]

            # start_time = first_item[0]
            # end_time = second_item[0]
            start_time = first_item.get_record().time
            end_time = second_item.get_record().time

            print("trying to create annotation from {0} to {1}".format(str(start_time), str(end_time)))
            # Since we don't know what the source for these global mark references are, we have to create a new annotation without any existing comment/config. This means the UI won't render it on a track by default.
            # currTrackWidget.create_comment_datetime(start_time, end_time)
            print("ERROR: UNIMPLMENTED: TODO: Create a generic annotation dialog (with a temporary config) and allow the user to add it even if the track isn't currently displayed)")
            return


    # Tries to create a comment between the two provided dates

    @pyqtSlot(datetime, datetime)
    def try_create_comment_between_dates(self, startDate, endDate):
        print("try_create_comment_between_dates(...)")
        start_time = startDate
        end_time = endDate

        print("trying to create annotation from {0} to {1}".format(str(start_time), str(end_time)))
        # Since we don't know what the source for these global mark references are, we have to create a new annotation without any existing comment/config. This means the UI won't render it on a track by default.
        # currTrackWidget.create_comment_datetime(start_time, end_time)
        print("ERROR: UNIMPLMENTED: TODO: Create a generic annotation dialog (with a temporary config) and allow the user to add it even if the track isn't currently displayed)")
        return





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

        if trackID in self.videoFileTrackWidgetHeaders.keys():
            # video file
            currVideoTrackHeader = self.videoFileTrackWidgetHeaders[trackID]
            currVideoTrackConfig = currVideoTrackHeader.get_config()
            self.activeTrackID_ConfigEditingIndex = trackID
            self.activeVideoTrackConfigEditDialog = VideoTrackFilterEditDialog(currVideoTrackConfig, parent=self)
            self.activeVideoTrackConfigEditDialog.on_commit.connect(self.try_update_video_track_filter)
            self.activeVideoTrackConfigEditDialog.on_cancel.connect(self.track_config_dialog_canceled)
            pass
        elif trackID in self.eventTrackWidgetHeaders.keys():
            # event track
            currTrackHeader = self.eventTrackWidgetHeaders[trackID]
            currTrackConfig = currTrackHeader.get_config()
            self.activeTrackID_ConfigEditingIndex = trackID
            self.activeVideoTrackConfigEditDialog = TrackFilterEditDialogBase(currTrackConfig, parent=self)
            self.activeVideoTrackConfigEditDialog.on_commit.connect(self.try_update_event_track_filter)
            self.activeVideoTrackConfigEditDialog.on_cancel.connect(self.track_config_dialog_canceled)
            pass
        else:
            print("WARNING: Couldn't find header with trackID: {0}".format(trackID))

    @pyqtSlot(int)
    def on_track_header_refresh_activated(self, trackID):
        print("on_track_header_refresh_activated({0})".format(trackID))

        if trackID in self.videoFileTrackWidgetHeaders.keys():
            #video track
            # currVideoTrackHeader = self.videoFileTrackWidgetHeaders[trackID]
            self.reload_videos_from_track_configs()
            pass
        elif trackID in self.eventTrackWidgetHeaders.keys():
            # event track
            currTrackHeader = self.eventTrackWidgetHeaders[trackID]
            currTrackConfig = currTrackHeader.get_config()
            currTrackWidget = None
            for i in range(0, len(self.eventTrackWidgets)):
                if (trackID == self.eventTrackWidgets[i].trackID):
                    currTrackWidget = self.eventTrackWidgets[i]
                    break
                else:
                    continue
            
            if (currTrackWidget is None):
                print("ERROR: couldn't get the active track widget with event trackID: {0}".format(trackID))
                return
            currTrackConfig.reload(self.database_connection.get_session(), currTrackWidget)
            self.update()
            pass
        else:
            print("Error: unknown track type!")
            return
    
    

    @pyqtSlot(int, object)
    def on_video_track_child_generate_thumbnails(self, trackID, videoDurationObj):
        print("TimelineDrawingWindow.on_video_track_child_generate_thumbnails({0}, {1})".format(str(trackID), str(videoDurationObj)))

        currTrackConfig = self.trackConfigurationsDict[trackID]
        currFoundTrack = self.get_track_with_trackID(trackID)

        # currSpecifiedChildItem = currFoundTrack[]
        proposed_video_file_path = videoDurationObj.get_full_path()
        if (proposed_video_file_path is not None):
            # Have a valid video file path
            print("TimelineDrawingWindow.on_video_track_child_generate_thumbnails(...): starting thumbnail generation with video: {0}...".format(str(proposed_video_file_path)))
            # Start thumbnail generation for this video file too:
            self.get_video_thumbnail_generator().add_video_path(str(proposed_video_file_path))

        else:
            print("TimelineDrawingWindow.on_video_track_child_generate_thumbnails(...): video URL can not be resolved. Perhaps the file doesn't exist?")
            return
            
        return



    @pyqtSlot(int, object)
    def on_track_child_get_info(self, trackID, commentObj):
        print("TimelineDrawingWindow.on_track_child_get_info({0}, {1})".format(str(trackID), str(commentObj)))
        # Find the correct config:
        pass



    @pyqtSlot(int, object)
    def on_track_child_create_comment(self, trackID, commentObj):
        print("TimelineDrawingWindow.on_track_child_create_comment({0}, {1})".format(str(trackID), str(commentObj)))
        # Find the correct config:
        if trackID in self.videoFileTrackWidgetHeaders.keys():
            #video track
            currTrackHeader = self.videoFileTrackWidgetHeaders[trackID]
            pass
        elif trackID in self.eventTrackWidgetHeaders.keys():
            # event track
            currTrackHeader = self.eventTrackWidgetHeaders[trackID]
            pass
        else:
            print("Error: unknown track type!")
            return

        currTrackConfig = currTrackHeader.get_config()
        currTrackFilter = currTrackConfig.get_filter()

        ## TODO: Convert to make use of my track groups helper objects.
        # Use the filter to find the matching annotations track if it exists
        found_dest_track_id = None
        for (aKey, currDestTrackHeader) in self.eventTrackWidgetHeaders.items():
            if aKey == trackID:
                # don't allow adding to the same track that called this function
                continue
            else:
                currDestTrackConfig = currDestTrackHeader.get_config()
                
                if (currDestTrackConfig.get_track_type() != TrackType.Annotation):
                    # wrong type
                    continue
                else:
                    # correct type
                    currDestTrackFilter = currDestTrackConfig.get_filter()
                    if currDestTrackFilter.matches(currTrackFilter):
                        # found filter
                        found_dest_track_id = aKey
                        break
                    else:
                        continue

        if found_dest_track_id is not None:
            print("Found matching annotation track! {0}".format(str(found_dest_track_id)))
            # Get the object properties
            sel_start = commentObj.startTime
            sel_endtime = commentObj.endTime
            # Call the create_annotation function on the track with found_dest_track_id
            print("trying to create annotation from {0} to {1}".format(str(sel_start), str(sel_endtime)))
            currTrackWidget = None
            for i in range(0, len(self.eventTrackWidgets)):
                if (found_dest_track_id == self.eventTrackWidgets[i].trackID):
                    currTrackWidget = self.eventTrackWidgets[i]
                    break
                else:
                    continue
            
            if (currTrackWidget is None):
                print("ERROR: couldn't get the active track widget with event trackID: {0}".format(trackID))
                return
            else:
                print("creating annotation....")
                currTrackWidget.create_comment_datetime(sel_start, sel_endtime)

        else:
            print("WARNING: Couldn't find matching annotation track for filter {0}".format(str(currTrackFilter)))
            return

        return

    # Called when the partition edit dialog accept event is called.
    @pyqtSlot(int, str, int, int, int, int, bool, bool)
    def try_update_video_track_filter(self, trackID, trackName, behavioral_box_id, experiment_id, cohort_id, animal_id, allow_original_videos, allow_labeled_videos):
        # Tries to update the video track config
        print('TimelineDrawingWindow.try_update_video_track_filter(...): track_id: {0}, track_name: {1}'.format(trackID, trackName))
        # if (not (self.trackContextConfig.get_is_valid())):
        #     print('context is invalid! aborting try_update_video!')
        #     return
        
        if (not (self.activeTrackID_ConfigEditingIndex is None)):
            currVideoTrackHeader = self.videoFileTrackWidgetHeaders[trackID]
            currVideoTrackConfig = currVideoTrackHeader.get_config()
            currVideoTrackFilter = currVideoTrackConfig.get_filter()

            # Convert -1 values for type_id and subtype_id back into "None" objects. They had to be an Int to be passed through the pyQtSlot()
            # Note the values are record IDs (not indicies, so they're 1-indexed). This means that both -1 and 0 are invalid.
            proposedModifiedFilter = VideoTrackFilter(allow_original_videos, allow_labeled_videos, None, None, None, None, parent=currVideoTrackConfig.parent())

            if (behavioral_box_id < 1):
                proposedModifiedFilter.behavioral_box_ids = None
            else:
                proposedModifiedFilter.behavioral_box_ids = [behavioral_box_id]


            if (experiment_id < 1):
                proposedModifiedFilter.experiment_ids = None
            else:
                proposedModifiedFilter.experiment_ids = [experiment_id]


            if (cohort_id < 1):
                proposedModifiedFilter.cohort_ids = None
            else:
                proposedModifiedFilter.cohort_ids = [cohort_id]

            if (animal_id < 1):
                proposedModifiedFilter.animal_ids = None
            else:
                proposedModifiedFilter.animal_ids = [animal_id]

            modifiedConfig = self.videoFileTrackWidgetHeaders[trackID].get_config()
            modifiedConfig.set_filter(proposedModifiedFilter)
            self.videoFileTrackWidgetHeaders[trackID].set_config(modifiedConfig)
            self.trackFloatingWidgetHeaders[trackID].update_labels_dynamically()

            self.reload_videos_from_track_configs()
            self.update()
        else:
            print("Error: unsure what video track config to update!")
            self.activeTrackID_ConfigEditingIndex = None
            return

        self.activeTrackID_ConfigEditingIndex = None


    @pyqtSlot(int, str, int, int, int, int)
    def try_update_event_track_filter(self, trackID, trackName, behavioral_box_id, experiment_id, cohort_id, animal_id):
        # Tries to update the event track config
        print('TimelineDrawingWindow.try_update_event_track_filter(...): track_id: {0}, track_name: {1}'.format(trackID, trackName))
        
        if (not (self.activeTrackID_ConfigEditingIndex is None)):
            currTrackHeader = self.eventTrackWidgetHeaders[trackID]
            currTrackConfig = currTrackHeader.get_config()
            currTrackFilter = currTrackConfig.get_filter()

            currTrackWidget = None
            for i in range(0, len(self.eventTrackWidgets)):
                if (trackID == self.eventTrackWidgets[i].trackID):
                    currTrackWidget = self.eventTrackWidgets[i]
                    break
                else:
                    continue
            
            if (currTrackWidget is None):
                print("ERROR: couldn't get the active track widget with event trackID: {0}".format(trackID))
                return



            # Convert -1 values for type_id and subtype_id back into "None" objects. They had to be an Int to be passed through the pyQtSlot()
            # Note the values are record IDs (not indicies, so they're 1-indexed). This means that both -1 and 0 are invalid.
            proposedModifiedFilter = TrackFilterBase(currTrackFilter.get_track_record_class(), None, None, None, None, parent=currTrackConfig.parent())

            if (behavioral_box_id < 1):
                proposedModifiedFilter.behavioral_box_ids = None
            else:
                proposedModifiedFilter.behavioral_box_ids = [behavioral_box_id]


            if (experiment_id < 1):
                proposedModifiedFilter.experiment_ids = None
            else:
                proposedModifiedFilter.experiment_ids = [experiment_id]


            if (cohort_id < 1):
                proposedModifiedFilter.cohort_ids = None
            else:
                proposedModifiedFilter.cohort_ids = [cohort_id]

            if (animal_id < 1):
                proposedModifiedFilter.animal_ids = None
            else:
                proposedModifiedFilter.animal_ids = [animal_id]

            modifiedConfig = self.eventTrackWidgetHeaders[trackID].get_config()
            modifiedConfig.set_filter(proposedModifiedFilter)
            self.eventTrackWidgetHeaders[trackID].set_config(modifiedConfig)
            self.trackFloatingWidgetHeaders[trackID].update_labels_dynamically()

            # TODO: Reload events
            modifiedConfig.reload(self.database_connection.get_session(), currTrackWidget)

            self.update()
        else:
            print("Error: unsure what event track config to update!")
            self.activeTrackID_ConfigEditingIndex = None
            return

        self.activeTrackID_ConfigEditingIndex = None

    @pyqtSlot()
    def track_config_dialog_canceled(self):
        print('track_config_dialog_canceled()')
        self.activeTrackID_ConfigEditingIndex = None

    # Sets the self.activeScaleMultiplier, then calls the updateViewportZoomFactorsUsingCurrentAdjustmentMode() function to update the corresponding quantity. If the value changes, emits the appropriate signals
    def set_new_active_scale_multiplier(self, newActiveScaleMultiplier):
        self.viewportAdjustmentMode = ViewportScaleAdjustmentOptions.MaintainDesiredViewportZoomFactor
        oldScaleMultiplier = self.activeScaleMultiplier
        if (newActiveScaleMultiplier != oldScaleMultiplier):
            # If the desired viewport duration is changing
            self.activeScaleMultiplier = newActiveScaleMultiplier
            self.updateViewportZoomFactorsUsingCurrentAdjustmentMode()
            self.activeZoomChanged.emit()
            self.activeViewportChanged.emit()
            self.minimumTimelineTrackWidthChanged.emit(self.get_minimum_track_width())
            self.update()

    # Sets the self.activeViewportDuration, then calls the updateViewportZoomFactorsUsingCurrentAdjustmentMode() function to update the corresponding quantity. If the value changes, emits the appropriate signals
    def set_new_desired_viewport_duration(self, newDesiredViewportDuration):
        self.viewportAdjustmentMode = ViewportScaleAdjustmentOptions.MaintainDesiredViewportDisplayDuration
        oldViewportDuration = self.activeViewportDuration

        if (newDesiredViewportDuration != oldViewportDuration):
            # If the desired viewport duration is changing
            self.activeViewportDuration = newDesiredViewportDuration
            
            self.updateViewportZoomFactorsUsingCurrentAdjustmentMode()
            self.activeZoomChanged.emit()
            self.activeViewportChanged.emit()
            self.minimumTimelineTrackWidthChanged.emit(self.get_minimum_track_width())
            self.update()

    """ updateViewportZoomFactorsUsingCurrentAdjustmentMode()
        Called to ensure that the corect activeViewportDuration and activeScaleMultiplier are set, given the current viewportAdjustmentMode.
        For example when the window is resized, the totalDuration changes, or the user specifies a different factor manually
    """
    def updateViewportZoomFactorsUsingCurrentAdjustmentMode(self, force_update=True):
        didUpdateZoomFactor = False

        oldViewportDuration = self.activeViewportDuration
        oldScaleMultiplier = self.activeScaleMultiplier

        if self.viewportAdjustmentMode is ViewportScaleAdjustmentOptions.MaintainDesiredViewportZoomFactor:
            # Compute the correct activeViewportDuration from the activeScaleMultiplier
            proposedViewportDuration = self.compute_current_desiredViewportDuration_from_activeScaleMultiplier(self.activeScaleMultiplier)
            if (force_update or (proposedViewportDuration != oldViewportDuration)):
                self.activeViewportDuration = proposedViewportDuration
                # print("TimelineDrawingWindow.updateViewportZoomFactorsUsingCurrentAdjustmentMode(): new value of activeScaleMultiplier {0} -- updated activeViewportDuration from {1} to {2}.".format(str(self.activeScaleMultiplier), str(oldViewportDuration), str(self.activeViewportDuration) ))
                didUpdateZoomFactor = True

            pass
        elif self.viewportAdjustmentMode is ViewportScaleAdjustmentOptions.MaintainDesiredViewportDisplayDuration:
            # Compute the correct activeScaleMultiplier from the activeViewportDuration
            proposedScaleMultiplier = self.compute_current_activeScaleMultiplier_from_desiredViewportDuration(self.activeViewportDuration)
            if (force_update or (proposedScaleMultiplier != oldScaleMultiplier)):
                self.activeScaleMultiplier = proposedScaleMultiplier
                # print("TimelineDrawingWindow.updateViewportZoomFactorsUsingCurrentAdjustmentMode(): new value of activeViewportDuration {0} -- updated activeScaleMultiplier from {1} to {2}.".format(str(self.activeViewportDuration), str(oldScaleMultiplier), str(self.activeScaleMultiplier) ))
                didUpdateZoomFactor = True
            pass
        else:
            print("FATAL ERROR: Invalid viewportAdjustmentMode!")
            return

        return didUpdateZoomFactor

    # The native PyQt5 Window resize event function that's called when the window is resized.
    def resizeEvent(self, event):
        self.window_resized.emit()
        return super().resizeEvent(event)

    @pyqtSlot()
    def on_window_resized(self):
        # print("window resized! newSize: {0}".format(str(self.width())))
        self.updateViewportZoomFactorsUsingCurrentAdjustmentMode()
        self.activeZoomChanged.emit()
        self.activeViewportChanged.emit()
        self.minimumTimelineTrackWidthChanged.emit(self.get_minimum_track_width())
        self.update()
        return

    # Called after self.activeScaleMultiplier is changed to update everything else
    @pyqtSlot()
    def on_active_zoom_changed(self):
        # print("TimelineDrawingWindow.on_active_zoom_changed(...)")
        self.updateViewportZoomFactorsUsingCurrentAdjustmentMode()
        # Update the UI to reflect the changes
        self.on_active_viewport_changed()
        self.resize_children_on_zoom()
        self.refresh_child_widget_display()

        # if (self.pending_adjust_viewport_start_datetime is not None):
        #     # Re-adjust the viewport's left edge
        #     self.sync_active_viewport_start_to_datetime(self.pending_adjust_viewport_start_datetime) # Use the saved start time to re-align the viewport's left edge
        #     self.pending_adjust_viewport_start_datetime = None
        

    @pyqtSlot()
    def on_active_viewport_changed(self):
        # print("TimelineDrawingWindow.on_active_viewport_changed(...)")
        self.updateViewportZoomFactorsUsingCurrentAdjustmentMode()
        # Update the UI to reflect the changes
        self.refreshUI_viewport_zoom_controls()
        self.refreshUI_viewport_info_labels()

        # self.timelineScroll.horizontalScrollBar().setPageStep()

    @pyqtSlot(int)
    def on_viewport_slider_changd(self, newValue):
        # print("TimelineDrawingWindow.on_viewport_slider_changd({0})".format(str(newValue)))
        self.refreshUI_viewport_info_labels()
        return

    @pyqtSlot(datetime, datetime, timedelta)
    def on_active_global_timeline_times_changed(self, totalStartTime, totalEndTime, totalDuration):
        print("TimelineDrawingWindow.on_active_global_timeline_times_changed({0}, {1}, {2})".format(str(totalStartTime), str(totalEndTime), str(totalDuration)))
        self.updateViewportZoomFactorsUsingCurrentAdjustmentMode()
        self.reload_tracks_from_track_configs()
        return


    # export_partition_track_to_file(): exports the specified partition track to one file per video file it overlaps.
    """
        For a given partition track, there should be a corresponding video track (and optionally a labeled video track) with one or more videos.
        For each video in these tracks, translate the datetime to a duration offset from the start of that video. 
    """
    def export_partition_track_to_file(self, partitionTrackID):
        print("TimelineDrawingWindow.export_partition_track_to_file(partitionTrackID: {0})".format(str(partitionTrackID)))
        
        pass

    @pyqtSlot()
    def on_user_data_export(self):
        # Called when the user selects "Export data..." from the main menu.
        print("TimelineDrawingWindow.on_user_data_export()")
        # Show a dialog that asks the user for their export path
        # exportFilePath = self.on_exportFile_selected()

        exportFolderPath = self.on_exportFilesToFolder_selected()
        if exportFolderPath == '':
            print("User canceled the export!")
            return

        # Get the video records for the currently displayed tracks.
        self.totalTrackCount = len(self.videoFileTrackWidgets) + len(self.eventTrackWidgets)
        self.totalNumGroups = len(self.trackGroups)

        # Loop through the groups to layout the tracks
        for currGroupIndex in range(0, self.totalNumGroups):
            currGroup = self.trackGroups[currGroupIndex]
            if currGroup.get_videoTrackIndex() is not None:
                currVideoTrackWidget = self.videoFileTrackWidgets[currGroup.get_videoTrackIndex()]

                # if currGroup.get_annotationsTrackIndex() is not None:
                #     currWidget = self.eventTrackWidgets[currGroup.get_annotationsTrackIndex()]

                    
                if currGroup.get_partitionsTrackIndex() is not None:
                    currWidget = self.eventTrackWidgets[currGroup.get_partitionsTrackIndex()]
                    currContainerArray = currWidget.get_cached_container_array()

                    currVideoContainerArray = currVideoTrackWidget.get_cached_container_array()
                    
                    # self.export_behavior_data_for_videos(exportFolderPath, currVideoContainerArray, currContainerArray, exportOptions=FileExportOptions.SingleFileForAllVideos)
                    self.export_behavior_data_for_videos(exportFolderPath, currVideoContainerArray, currContainerArray, exportOptions=FileExportOptions.FilePerVideo)
                else:
                    print("No matching partition track for group {0}. Nothing to export.".format(str(currGroupIndex)))

            else:
                print("Group {0} has no video track! Skipping; nothing to export.".format(str(currGroupIndex)))
            



        # Iterate through all video files and find the partition events that overlap them.
        # for aVideoInfoObj in self.video:
        #     pass

    def get_video_thumbnail_generator(self):
        return self.videoThumbnailGenerator

    # on_video_thumbnail_generation_complete(): Called when a thumbnail generation is complete for a given video
    @pyqtSlot()
    def on_video_thumbnail_generation_complete(self):
        print("TimelineDrawingWindow.on_video_thumbnail_generation_complete()...")
        # Clear the top-level nodes
        self.video_thumbnail_popover_window = QDialog(self)
        # self.video_thumbnail_popover_window.setCentr
        # A vertical box layout
        thumbnailsLayout = QVBoxLayout()

        desiredThumbnailSizeKey = "40"

        # for (aSearchPathIndex, aSearchPath) in enumerate(self.searchPaths):
        for (key_path, cache_value) in self.get_video_thumbnail_generator().get_cache().items():
            # key_path: the video file path that had the thumbnails generated for it
            print("thumbnail generation complete for [{0}]: {1} frames".format(str(key_path), len(cache_value)))
            for (index, aVideoThumbnailObj) in enumerate(cache_value):
                currThumbsDict = aVideoThumbnailObj.get_thumbs_dict()
                # currThumbnailImage: should be a QImage
                currThumbnailImage = currThumbsDict[desiredThumbnailSizeKey]
                w = QLabel()
                w.setPixmap(QtGui.QPixmap.fromImage(currThumbnailImage))
                thumbnailsLayout.addWidget(w)

        
        self.video_thumbnail_popover_window.setLayout(thumbnailsLayout)
        self.video_thumbnail_popover_window.show()

        self.update()
    