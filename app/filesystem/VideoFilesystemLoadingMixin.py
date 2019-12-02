# VideoFilesystemLoadingMixin.py
import sys
from datetime import datetime, timezone, timedelta
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingQObject

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult
from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker, VideoMetadataWorkerSignals
from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker, VideoFilesystemWorkerSignals

from pathlib import Path

# from app.filesystem.VideoFilesystemLoadingMixin import CachedVideoFileLoadingOptions, ParentDirectoryCache, VideoFilesystemLoadingMixin

class CachedVideoFileLoadingOptions(Enum):
        LoadOnlyFromDatabase = 1 # Only loads the video file records from the sqlite database. Doesn't search the disk for new video files or update existing ones
        LoadDatabaseAndSearchVideoFileSearchPaths = 2 #  Load the video file records from the sqlite database AND search the video file search paths for new or updated video files.



class ParentDirectoryCache(QObject):
    def __init__(self, full_path):
        super(ParentDirectoryCache, self).__init__(None)
        self.full_path = full_path

        self.database_parent_folder_obj = None
        self.database_video_files = []
        
        self.found_filesystem_video_files = []
        self.finalOutputParsedVideoResultFiles = []

    def get_full_path(self):
        return str(self.full_path)

    def get_path_obj(self):
        return Path(self.get_full_path()).resolve()

    def get_root_anchor(self):
        return self.get_path_obj().anchor

    def get_non_root_remainder(self):
        currPath = self.get_path_obj()
        return currPath.relative_to(self.get_root_anchor())

    def set_database_video_files(self, new_db_video_files):
        self.database_video_files = new_db_video_files
        for aLoadedVideoFileRecord in self.database_video_files:
            newObj = aLoadedVideoFileRecord.get_parsed_video_result_obj()
            self.finalOutputParsedVideoResultFiles.append(newObj)

    def set_found_filesystem_video_files(self, new_found_filesystem_video_files):
        self.found_filesystem_video_files = new_found_filesystem_video_files
        for aLoadedVideoFileRecord in self.found_filesystem_video_files:
            self.finalOutputParsedVideoResultFiles.append(aLoadedVideoFileRecord)
        
    def get_filesystem_video_files(self):
        return self.found_filesystem_video_files

    def get_database_video_files(self):
        return self.database_video_files

    def set_database_parent_folder_obj(self, new_db_parent):
        self.database_parent_folder_obj = new_db_parent

    def get_database_parent_folder(self):
        return self.database_parent_folder_obj

    def get_combined_video_files(self):
        return self.finalOutputParsedVideoResultFiles




## This "Mixin" adds these columns and relationships to any file that inherits from it
# See https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/mixins.html for more info
class VideoFilesystemLoadingMixin(object):

    VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths

    # def __init__(self, database_connection, videoFileSearchPaths):
    #     self.cache = dict()
    #     self.searchPaths = videoFileSearchPaths
    #     self.reload_on_search_paths_changed()
    #     self.threadpool = QThreadPool()
    #     print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
    #     self.reload_data()

    def reload_on_search_paths_changed(self):
        self.reloadModelFromDatabase()
        self.rebuildParentFolders()

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


    ## CALLBACK FUNCTIONS:
    ## Find_video_metadata:
    def on_find_video_metadata_progress_fn(self, n):
        print("%d%% done" % n)

    def on_find_video_metadata_execute_thread(self, progress_callback):
        currProgress = 0.0
        parsedFiles = 0
        for (key_path, cache_value) in self.cache.items():
            # Iterate through all found file-lists
            for (sub_index, aFoundVideoFile) in enumerate(cache_value.get_filesystem_video_files()):
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
        # self.found_files_lists = []
        # TODO: clear old files from cache?
        self.total_found_files = 0
        self.total_search_paths = len(self.searchPaths)

        # Clear the top-level nodes
        for aSearchPath in self.searchPaths:
            curr_search_path_video_files = findVideoFiles(aSearchPath, shouldPrint=False)
            # self.found_files_lists.append(curr_search_path_video_files)
            self.cache[aSearchPath].set_found_filesystem_video_files(curr_search_path_video_files)
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