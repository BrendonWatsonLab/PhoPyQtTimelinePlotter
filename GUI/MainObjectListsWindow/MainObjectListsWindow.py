# EventsDrawingWindow.py
# Draws the main window containing several EventTrackDrawingWidgets

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool


from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWindow

from app.database.SqliteEventsDatabase import load_video_events_from_database
from app.database.SqlAlchemyDatabase import load_annotation_events_from_database, save_annotation_events_to_database, create_TimestampedAnnotation

from app.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult, VideoMetadataWorker, VideoMetadataWorkerSignals

class MainObjectListsWindow(AbstractDatabaseAccessingWindow):
    
    def __init__(self, database_connection, videoFileSearchPaths):
        super(MainObjectListsWindow, self).__init__(database_connection) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/MainObjectListsWindow/MainObjectListsWindow.ui", self) # Load the .ui file

        self.searchPaths = videoFileSearchPaths
        self.top_level_nodes = []
        self.found_files_lists = []

        # self.videoInfoObjects = load_video_events_from_database(self.database_connection.get_path(), as_videoInfo_objects=True)
        # self.build_video_display_events()

        # self.video_files = findVideoFiles(self.searchPaths[0], shouldPrint=True)

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())


        self.setMouseTracking(True)
        self.initUI()

        self.rebuild_from_search_paths()
        self.find_video_metadata()
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
            self.ui.actionLoad.triggered.connect(self.handle_menu_load_event)
            self.ui.actionSave.triggered.connect(self.handle_menu_save_event)
            self.ui.actionRefresh.triggered.connect(self.handle_menu_refresh_event)
            


        desiredWindowWidth = 500
        self.resize( desiredWindowWidth, 800 )

        # Setup the menubar
        initUI_initMenuBar(self)

        # Setup the tree
        # self.ui.treeWidget_VideoFiles

        self.ui.textBrowser_SelectedInfoBox.setText("Hi")

        # Main Vertical Splitter:
        self.ui.mainVerticalSplitter.setSizes([700, 100])

        # Complete setup
        self.statusBar()


    def rebuild_from_search_paths(self):
        self.ui.treeWidget_VideoFiles.clear()
        self.top_level_nodes = []
        self.found_files_lists = []
        self.total_found_files = 0

        # Clear the top-level nodes
        for aSearchPath in self.searchPaths:        
            aNewGroupNode = QTreeWidgetItem([str(aSearchPath), '', '', ''])
            curr_search_path_video_files = findVideoFiles(aSearchPath, shouldPrint=False)
            self.found_files_lists.append(curr_search_path_video_files)
            for aFoundVideoFile in curr_search_path_video_files:
                # aFoundVideoFile.parse()
                potentially_computed_end_date = aFoundVideoFile.get_computed_end_date()
                if potentially_computed_end_date:
                    computed_end_date = str(potentially_computed_end_date)
                else:
                    computed_end_date = 'Loading...'
                # aNewVideoNode = QTreeWidgetItem([str(aFoundVideoFile.full_name), str(aFoundVideoFile.parsed_date), str(aFoundVideoFile.get_computed_end_date()), str(aFoundVideoFile.is_deeplabcut_labeled_video)])
                aNewVideoNode = QTreeWidgetItem([str(aFoundVideoFile.full_name), str(aFoundVideoFile.parsed_date), computed_end_date, str(aFoundVideoFile.is_deeplabcut_labeled_video)])
                aNewGroupNode.addChild(aNewVideoNode)
                self.total_found_files = self.total_found_files + 1

            self.top_level_nodes.append(aNewGroupNode)
            
            # Eventually will call .parse() on each of them to populate the duration info and end-times. This will be done asynchronously.
        self.ui.treeWidget_VideoFiles.addTopLevelItems(self.top_level_nodes)


    # Finds the video metadata in a multithreaded way
    def find_video_metadata(self):
        # Pass the function to execute
        worker = VideoMetadataWorker(self.execute_find_video_metadata_thread) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        
        # Execute
        self.threadpool.start(worker) 


    # Event Handlers:
    def keyPressEvent(self, event):
        pass
        
    def mouseMoveEvent(self, event):
        pass


    def handle_menu_load_event(self):
        print("actionLoad")
        pass

    def handle_menu_save_event(self):
        print("actionSave")
        pass

    def handle_menu_refresh_event(self):
        print("actionRefresh")
        pass


    def progress_fn(self, n):
        print("%d%% done" % n)

    def execute_find_video_metadata_thread(self, progress_callback):
        currProgress = 0.0
        parsedFiles = 0
        for (index, fileList) in enumerate(self.found_files_lists):
            # Iterate through all found file-lists
            for (sub_index, aFoundVideoFile) in enumerate(fileList):
                # Iterate through all found video-files in a given list
                aFoundVideoFile.parse()
                parsedFiles = parsedFiles + 1
                progress_callback.emit(parsedFiles*100/self.total_found_files)


        return "Done."
 
    def print_output(self, s):
        print(s)
        
    def thread_complete(self):
        print("THREAD COMPLETE!")
        self.rebuild_from_search_paths()


    def update_end_date(self, top_level_index, child_index, new_date):
        curr_top_level_node = self.top_level_nodes[top_level_index]
        curr_child_node = curr_top_level_node.child(child_index)
        curr_child_node.setText(2, new_date)

        # for (aTopLevelNodeIndex, aTopLevelNode) in enumerate(self.top_level_nodes):        
        #     curr_search_path_video_files = self.found_files_lists[aTopLevelNodeIndex]

        #     for aFoundVideoFile in curr_search_path_video_files:
        #         # aFoundVideoFile.parse()
        #         # aNewVideoNode = QTreeWidgetItem([str(aFoundVideoFile.full_name), str(aFoundVideoFile.parsed_date), str(aFoundVideoFile.get_computed_end_date()), str(aFoundVideoFile.is_deeplabcut_labeled_video)])
        #         aNewVideoNode = QTreeWidgetItem([str(aFoundVideoFile.full_name), str(aFoundVideoFile.parsed_date), 'Loading...', str(aFoundVideoFile.is_deeplabcut_labeled_video)])
        #         aNewGroupNode.addChild(aNewVideoNode)
        #         self.total_found_files = self.total_found_files + 1


    # @pyqtSlot(int, int)
    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_selection_event(self, trackIndex, trackObjectIndex):
       pass

    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_hover_event(self, trackIndex, trackObjectIndex):
        pass

    def refresh_child_widget_display(self):
        pass


    
