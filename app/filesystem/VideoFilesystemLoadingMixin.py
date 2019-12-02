# VideoFilesystemLoadingMixin.py
import sys
from datetime import datetime, timezone, timedelta
from enum import Enum

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingQObject

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult
from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker, VideoMetadataWorkerSignals
from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker, VideoFilesystemWorkerSignals

from pathlib import Path

from app.database.entry_models.db_model import FileParentFolder, StaticFileExtension, VideoFile
from app.filesystem.VideoConversionHelpers import HandbrakeConversionQueue, save_handbrake_conversion_queue

# from app.filesystem.VideoFilesystemLoadingMixin import CachedVideoFileLoadingOptions, ParentDirectoryCache, VideoFilesystemLoader

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




## VideoFilesystemLoader: this object tries to find video files in the filesystem and add them to the database if they don't exist
"""
Loads the VideoFiles from the database (cached versions) and then tries to search the filesystem for additional video files.
"""
class VideoFilesystemLoader(AbstractDatabaseAccessingQObject):

    VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths


    foundFilesUpdated = pyqtSignal()

    findMetadataComplete = pyqtSignal()
    findVideosComplete = pyqtSignal()

    def __init__(self, database_connection, videoFileSearchPaths, parent=None):
        super(VideoFilesystemLoader, self).__init__(database_connection, parent=parent) # Call the inherited classes __init__ method
        self.cache = dict()
        self.loadedParentFolders = []
        self.loadedVideoFiles = []

        self.searchPaths = videoFileSearchPaths
        self.reload_on_search_paths_changed()
        
        self.videoFilesystemWorker = None
        self.videoMetadataWorker = None
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.reload_data()




    ## DATABASE Functions:
    

    def reload_data(self):
        # Load the video files depending on the setting.
        if VideoFilesystemLoader.VideoFileLoadingMode == CachedVideoFileLoadingOptions.LoadOnlyFromDatabase:
            print("Only loading video files from database. Ignoring search paths...")
            self.rebuild_from_found_files()
        elif VideoFilesystemLoader.VideoFileLoadingMode == CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths:
            print("Loading video files from database and searching search paths...")
            self.find_filesystem_video()
        else:
            print("VideoFilesystemLoader ERROR: Unexpected enum type!")
            pass

    # TODO: should build parent nodes from a combination of the loaded parents and the search paths (if we're in a mode to load search paths)
    
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        self.fileExtensionDict = self.database_connection.load_static_file_extensions_from_database()
        self.loadedParentFolders = self.database_connection.load_file_parent_folders_from_database(include_video_files=True)
        self.loadedVideoFiles = []

        # Iterate through all found parent folders, replacing the versions in the cache with the ones from the database
        for aLoadedParentFolder in self.loadedParentFolders:
            self.cache[aLoadedParentFolder.fullpath] = ParentDirectoryCache(aLoadedParentFolder.fullpath)
            loadedVideoFiles = aLoadedParentFolder.videoFiles
            self.cache[aLoadedParentFolder.fullpath].set_database_parent_folder_obj(aLoadedParentFolder)
            self.cache[aLoadedParentFolder.fullpath].set_database_video_files(loadedVideoFiles)

        self.foundFilesUpdated.emit()


    def reload_on_search_paths_changed(self):
        self.reloadModelFromDatabase()
        self.rebuildParentFolders()

        self.foundFilesUpdated.emit()


    def saveVideoFilesToDatabase(self):
        for (key_path, cache_value) in self.cache.items():
            loaded_parent_folder_obj = cache_value.get_database_parent_folder()
            curr_search_path_video_files = cache_value.get_filesystem_video_files()
            existing_database_video_files = cache_value.get_database_video_files()
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
        # self.searchPathsParentIDs = []

        for (index, aSearchPath) in enumerate(unresolvedSearchPaths):
            currPath = Path(aSearchPath).resolve()
            currRootAnchor = currPath.anchor
            currRemainder = currPath.relative_to(currRootAnchor)
            print("currPath: {0}; currRootAnchor: {1}; currRemainder: {2}".format(currPath, currRootAnchor, currRemainder))
            
            aFinalSearchPath = str(currPath)
            self.searchPaths[index] = aFinalSearchPath

            if (not (aFinalSearchPath in self.cache.keys())):
                # Parent doesn't yet exist in cache
                self.cache[aFinalSearchPath] = ParentDirectoryCache(aFinalSearchPath)
            else:
                # Parent already exists
                self.cache[aFinalSearchPath]
            

            # Iterate through all loaded parents to see if the parent already exists
            finalParent = None
            
            # Database folders
            for aParentFolder in self.loadedParentFolders:
                aParentPath = Path(aParentFolder.fullpath).resolve()
                # Try to match to the loaded parent objects from the database
                self.cache[aFinalSearchPath]

                if aParentPath.samefile(currPath):
                    # currPath is the same file as the loaded parent path
                    print("Found existing parent for {0}".format(currPath))
                    finalParent = aParentFolder

            # If we get through all loaded parents and the parent doesn't already exist, add it
            if finalParent is None:
                print("Creating new parent {0}".format(currPath))
                finalParent = FileParentFolder(None, currPath, currRootAnchor, currRemainder, 'auto')
                # Save parent to database
                self.database_connection.save_file_parent_folders_to_database([finalParent])
                # Set parent to the newly created database parent object
                self.cache[aFinalSearchPath].set_database_parent_folder_obj(finalParent)

            if finalParent is None:
                print("Still nONE!")
                # self.searchPathsParentIDs.append(None)
                self.cache[aFinalSearchPath].set_database_parent_folder_obj(None)
            else:
                print("     parent id: {0}".format(finalParent.id))
                # self.searchPathsParentIDs.append(finalParent.id)
                self.cache[aFinalSearchPath].set_database_parent_folder_obj(finalParent)



    ## Primary Filesystem Functions
    # Finds the video files in the self.searchPaths in a multithreaded way
    def find_filesystem_video(self):
        # Pass the function to execute
        self.videoFilesystemWorker = VideoFilesystemWorker(self.on_find_filesystem_video_execute_thread) # Any other args, kwargs are passed to the run function
        self.videoFilesystemWorker.signals.result.connect(self.on_find_filesystem_video_print_output)
        self.videoFilesystemWorker.signals.finished.connect(self.on_find_filesystem_video_thread_complete)
        self.videoFilesystemWorker.signals.progress.connect(self.on_find_filesystem_video_progress_fn)
        
        # Execute
        self.threadpool.start(self.videoFilesystemWorker) 


    # Finds the video metadata in a multithreaded way
    def find_video_metadata(self):
        # Pass the function to execute
        self.videoMetadataWorker = VideoMetadataWorker(self.on_find_video_metadata_execute_thread) # Any other args, kwargs are passed to the run function
        self.videoMetadataWorker.signals.result.connect(self.on_find_video_metadata_print_output)
        self.videoMetadataWorker.signals.finished.connect(self.on_find_video_metadata_thread_complete)
        self.videoMetadataWorker.signals.progress.connect(self.on_find_video_metadata_progress_fn)
        
        # Execute
        self.threadpool.start(self.videoMetadataWorker) 


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
        self.findMetadataComplete.emit()
        # self.rebuild_from_found_files()


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
        # self.rebuild_from_found_files()
        self.findVideosComplete.emit()
        # Find the metadata for all the video
        self.find_video_metadata()