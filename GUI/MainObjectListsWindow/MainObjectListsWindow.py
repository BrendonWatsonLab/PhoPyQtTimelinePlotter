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

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult
from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker, VideoMetadataWorkerSignals
from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker, VideoFilesystemWorkerSignals

from pathlib import Path

from app.database.entry_models.db_model import FileParentFolder, StaticFileExtension, VideoFile

class CachedVideoFileLoadingOptions(Enum):
        LoadOnlyFromDatabase = 1 # Only loads the video file records from the sqlite database. Doesn't search the disk for new video files or update existing ones
        LoadDatabaseAndSearchVideoFileSearchPaths = 2 #  Load the video file records from the sqlite database AND search the video file search paths for new or updated video files.



class MainObjectListsWindow(AbstractDatabaseAccessingWindow):

    VideoFileTreeHeaderLabels = ['filename', 'start_date', 'end_date', 'is_labeled']
    
    VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadOnlyFromDatabase
    # VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths
    

    def __init__(self, database_connection, videoFileSearchPaths):
        super(MainObjectListsWindow, self).__init__(database_connection) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/MainObjectListsWindow/MainObjectListsWindow.ui", self) # Load the .ui file

        self.searchPaths = videoFileSearchPaths
        self.found_files_lists = []
        self.reloadModelFromDatabase()

        # self.searchPathsParentIDs: indexes into the database's fileParentFolders table.
        self.searchPathsParentIDs = []
        self.rebuildParentFolders()

        self.top_level_nodes = []


        # self.videoInfoObjects = load_video_events_from_database(self.database_connection.get_path(), as_videoInfo_objects=True)
        # self.build_video_display_events()

        # self.video_files = findVideoFiles(self.searchPaths[0], shouldPrint=True)

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.setMouseTracking(True)
        self.initUI()

        # Load the video files depending on the setting.
        if MainObjectListsWindow.VideoFileLoadingMode == CachedVideoFileLoadingOptions.LoadOnlyFromDatabase:
            print("Only loading video files from database. Ignoring search paths...")
            self.rebuild_from_found_files()
        elif MainObjectListsWindow.VideoFileLoadingMode == CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths:
            print("Loading video files from database and searching search paths...")
            self.find_filesystem_video()
        else:
            print("MainObjectListsWindow ERROR: Unexpected enum type!")
            pass
        
        
        
        

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
        self.ui.treeWidget_VideoFiles.setHeaderLabels(MainObjectListsWindow.VideoFileTreeHeaderLabels)

        self.ui.textBrowser_SelectedInfoBox.setText("Hi")

        # Main Vertical Splitter:
        self.ui.mainVerticalSplitter.setSizes([700, 100])

        # Setup the buttons
        # self.ui.pushButton_AddSearchDirectory.onClicked(self.handle_add_search_directory_activated)

        # Complete setup
        self.statusBar()


    # TODO: should build parent nodes from a combination of the loaded parents and the search paths (if we're in a mode to load search paths)
    
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        self.fileExtensionDict = self.database_connection.load_static_file_extensions_from_database()
        self.loadedParentFolders = self.database_connection.load_file_parent_folders_from_database(include_video_files=True)
        self.loadedVideoFiles = []

        for aLoadedParentFolder in self.loadedParentFolders:
            loadedVideoFiles = aLoadedParentFolder.videoFiles
            currOutList = []
            for aLoadedVideoFileRecord in loadedVideoFiles:
                self.loadedVideoFiles.append(aLoadedVideoFileRecord)
                newObj = aLoadedVideoFileRecord.get_parsed_video_result_obj()
                currOutList.append(newObj)
            self.found_files_lists.append(currOutList)


            #TODO: parse loadedVideoFiles into the regular objects that are loaded, and then add them to the self.found_files_lists
            # self.found_files_lists.append()

        # self.loadedVideoFiles = self.database_connection.load_video_file_info_from_database()



    def saveVideoFilesToDatabase(self):

        for (aSearchPathIndex, aSearchPath) in enumerate(self.searchPaths):        
            parentIDIndex = self.searchPathsParentIDs[aSearchPathIndex]
            if parentIDIndex is None:
                # Get the shared parent ID
                print("ERROR: parent ID is NONE!")
                continue

            arrayIndex = parentIDIndex - 1 # Convert from the database ID to the array of loaded parent object's index
            loaded_parent_folder_obj = self.loadedParentFolders[arrayIndex]
            
            curr_search_path_video_files = self.found_files_lists[aSearchPathIndex]
            existing_database_video_files = loaded_parent_folder_obj.videoFiles

            for aFoundVideoFile in curr_search_path_video_files:
                # Get the appropriate file extension parent
                currFileExtension = aFoundVideoFile.file_extension[1:].lower()
                parent_file_extension_obj = None
                if currFileExtension in self.fileExtensionDict.keys():
                    parent_file_extension_obj = self.fileExtensionDict[currFileExtension]
                else:
                    # Key doesn't exist!
                    print("extension {0} doesn't exist!".format(currFileExtension))
                    parent_file_extension_obj = StaticFileExtension(currFileExtension)
                    # Add it to the database
                    self.database_connection.save_static_file_extensions_to_database([parent_file_extension_obj])


                potentially_computed_end_date = aFoundVideoFile.get_computed_end_date()
                if potentially_computed_end_date:
                    computed_end_date = str(potentially_computed_end_date)
                else:
                    computed_end_date = 'Loading...'


                # Check if the videoFile exists:
                need_create_new_video_file = True
                for anExistingVideoFile in existing_database_video_files:
                    if (anExistingVideoFile.file_fullname == aFoundVideoFile.full_name):
                        # print("File already exists, skipping...")
                        need_create_new_video_file = False
                        break
                    else:
                        continue

                if need_create_new_video_file:
                    # Create the video file if needed
                    
                    aNewVideoFileRecord = VideoFile.from_parsed_video_result_obj(aFoundVideoFile,None,None,None,'auto')
                    # aNewVideoFileRecord = aFoundVideoFile.get_database_videoFile_record(None,None,None,'auto')
                    aNewVideoFileRecord.staticFileExtension = parent_file_extension_obj
                    aNewVideoFileRecord.fileParentFolder = loaded_parent_folder_obj

                    # Add the video file record
                    self.database_connection.save_video_file_info_to_database([aNewVideoFileRecord])




    # Creates new "FileParentFolder" entries in the databse if existing ones can't be found
    def rebuildParentFolders(self):
        unresolvedSearchPaths = self.searchPaths
        
        self.searchPathsParentIDs = []

        for (index, aSearchPath) in enumerate(unresolvedSearchPaths):
            currPath = Path(aSearchPath).resolve()
            currRootAnchor = currPath.anchor
            currRemainder = currPath.relative_to(currRootAnchor)
            print("currPath: {0}; currRootAnchor: {1}; currRemainder: {2}".format(currPath, currRootAnchor, currRemainder))
            self.searchPaths[index] = str(currPath)

            # Iterate through all loaded parents to see if the parent already exists
            finalParent = None
            
            # Database folders
            for aParentFolder in self.loadedParentFolders:
                aParentPath = Path(aParentFolder.fullpath).resolve()
                if aParentPath.samefile(currPath):
                    # currPath is the same file as the loaded parent path
                    print("Found existing parent for {0}".format(currPath))
                    finalParent = aParentFolder
            # If we get through all loaded parents and the parent doesn't already exist, add it
            if finalParent is None:
                print("Creating new parent {0}".format(currPath))
                finalParent = FileParentFolder(None, currPath, currRootAnchor, currRemainder, 'auto')
                self.database_connection.save_file_parent_folders_to_database([finalParent])

            if finalParent is None:
                print("Still nONE!")
                self.searchPathsParentIDs.append(None)
            else:
                print("     parent id: {0}".format(finalParent.id))
                self.searchPathsParentIDs.append(finalParent.id)


    # Rebuilds the entire Tree UI from the self.found_files_lists
    def rebuild_from_found_files(self):
        self.ui.treeWidget_VideoFiles.clear()
        self.top_level_nodes = []

        # Clear the top-level nodes
        for (aSearchPathIndex, aSearchPath) in enumerate(self.searchPaths):        
            aNewGroupNode = QTreeWidgetItem([str(aSearchPath), '', '', ''])
            curr_search_path_video_files = self.found_files_lists[aSearchPathIndex]

            for aFoundVideoFile in curr_search_path_video_files:
                potentially_computed_end_date = aFoundVideoFile.get_computed_end_date()
                if potentially_computed_end_date:
                    computed_end_date = str(potentially_computed_end_date)
                else:
                    computed_end_date = 'Loading...'
                aNewVideoNode = QTreeWidgetItem([str(aFoundVideoFile.full_name), str(aFoundVideoFile.parsed_date), computed_end_date, str(aFoundVideoFile.is_deeplabcut_labeled_video)])
                aNewGroupNode.addChild(aNewVideoNode)

            self.top_level_nodes.append(aNewGroupNode)
            
            # Eventually will call .parse() on each of them to populate the duration info and end-times. This will be done asynchronously.
        self.ui.treeWidget_VideoFiles.addTopLevelItems(self.top_level_nodes)
        # Expand all items
        self.expand_top_level_nodes()


    def expand_top_level_nodes(self):
        for aTopLevelItem in self.top_level_nodes:
            self.ui.treeWidget_VideoFiles.expandItem(aTopLevelItem)

    # Finds the video files in the self.searchPaths in a multithreaded way
    def find_filesystem_video(self):
        # Pass the function to execute
        worker = VideoFilesystemWorker(self.on_find_filesystem_video_execute_thread) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.on_find_filesystem_video_print_output)
        worker.signals.finished.connect(self.on_find_filesystem_video_thread_complete)
        worker.signals.progress.connect(self.on_find_filesystem_video_progress_fn)
        
        # Execute
        self.threadpool.start(worker) 


    # Finds the video metadata in a multithreaded way
    def find_video_metadata(self):
        # Pass the function to execute
        worker = VideoMetadataWorker(self.on_find_video_metadata_execute_thread) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.on_find_video_metadata_print_output)
        worker.signals.finished.connect(self.on_find_video_metadata_thread_complete)
        worker.signals.progress.connect(self.on_find_video_metadata_progress_fn)
        
        # Execute
        self.threadpool.start(worker) 

    # TODO: update end_date without rebuilding the whole table
    def update_end_date(self, top_level_index, child_index, new_date):
        curr_top_level_node = self.top_level_nodes[top_level_index]
        curr_child_node = curr_top_level_node.child(child_index)
        curr_child_node.setText(2, new_date)



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
        self.saveVideoFilesToDatabase()
        pass

    def handle_menu_refresh_event(self):
        print("actionRefresh")
        pass

    ## Find_video_metadata:
    def on_find_video_metadata_progress_fn(self, n):
        print("%d%% done" % n)

    def on_find_video_metadata_execute_thread(self, progress_callback):
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
 
    def on_find_video_metadata_print_output(self, s):
        print(s)
        
    def on_find_video_metadata_thread_complete(self):
        print("THREAD COMPLETE!")
        self.rebuild_from_found_files()


    ## FILESYSTEM:
    def on_find_filesystem_video_progress_fn(self, n):
        print("%d%% done" % n)

    def on_find_filesystem_video_execute_thread(self, progress_callback):
        searchedSearchPaths = 0
        self.found_files_lists = []
        self.total_found_files = 0
        self.total_search_paths = len(self.searchPaths)

        # Clear the top-level nodes
        for aSearchPath in self.searchPaths:
            curr_search_path_video_files = findVideoFiles(aSearchPath, shouldPrint=False)
            self.found_files_lists.append(curr_search_path_video_files)
            self.total_found_files = self.total_found_files + len(curr_search_path_video_files)
            searchedSearchPaths = searchedSearchPaths + 1
            progress_callback.emit(searchedSearchPaths*100/self.total_search_paths)

        return "Done."
 
    def on_find_filesystem_video_print_output(self, s):
        print(s)
        
    def on_find_filesystem_video_thread_complete(self):
        print("THREAD COMPLETE!")
        # Returned results in self.found_files_lists
        self.rebuild_from_found_files()
        # Find the metadata for all the video
        self.find_video_metadata()
        
    def handle_add_search_directory_activated(self):
        print("handle_add_search_directory_activated")
        

    # @pyqtSlot(int, int)
    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_selection_event(self, trackIndex, trackObjectIndex):
       pass

    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_hover_event(self, trackIndex, trackObjectIndex):
        pass

    def refresh_child_widget_display(self):
        pass


    
