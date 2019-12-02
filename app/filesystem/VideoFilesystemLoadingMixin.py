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

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult, CachedFileSource
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
    def __init__(self, full_path, source=CachedFileSource.Unknown, parent=None):
        super(ParentDirectoryCache, self).__init__(parent)
        self.full_path = full_path
        self.source = source
        
        self.database_parent_folder_obj = None
        self.database_video_files = []
        
        self.found_filesystem_video_files = []

        self.finalOutputParsedVideoResultFileSources = dict()
        self.finalOutputParsedVideoResultFiles = []

    def get_full_path(self):
        return str(self.full_path)

    def get_source(self):
        return self.source

    def set_source(self, new_source):
        self.source = new_source

    def get_path_obj(self):
        return Path(self.get_full_path()).resolve()

    def get_root_anchor(self):
        return self.get_path_obj().anchor

    def get_non_root_remainder(self):
        currPath = self.get_path_obj()
        return currPath.relative_to(self.get_root_anchor())

    def set_database_video_files(self, new_db_video_files):
        self.database_video_files = new_db_video_files
        self.rebuild_combined_video_files()

    def set_found_filesystem_video_files(self, new_found_filesystem_video_files):
        self.found_filesystem_video_files = new_found_filesystem_video_files
        self.rebuild_combined_video_files()
        
    def get_filesystem_video_files(self):
        return self.found_filesystem_video_files

    def get_database_video_files(self):
        return self.database_video_files

    def set_database_parent_folder_obj(self, new_db_parent):
        self.database_parent_folder_obj = new_db_parent

    def get_database_parent_folder(self):
        return self.database_parent_folder_obj

    # Called to build an array of both database and filesystem video files. They are meant to be unique.
    def rebuild_combined_video_files(self):
        self.finalOutputParsedVideoResultFileSources = dict()
        self.finalOutputParsedVideoResultFiles = []

        finalOutputParsedVideoResultFilesDict = dict()
        finalOutputParsedVideoResultFilesList = []

        # Database:
        for aLoadedDatabaseVideoFileRecord in self.database_video_files:
            newObj = aLoadedDatabaseVideoFileRecord.get_parsed_video_result_obj()
            newFullName = newObj.get_full_name()
            
            if newFullName in self.finalOutputParsedVideoResultFileSources.keys():
                print("ERROR: this should be impossible! We just cleared the finalOutputParsedVideoResultFileSources!")
                pass
            else:
                self.finalOutputParsedVideoResultFileSources[newFullName] = CachedFileSource.OnlyFromDatabase
                newObj.set_source(self.finalOutputParsedVideoResultFileSources[newFullName])
                finalOutputParsedVideoResultFilesDict[newFullName] = newObj

            # self.finalOutputParsedVideoResultFiles.append(newObj)

        should_add_curr_record = False

        # Filesystem:
        for aLoadedFilesystemVideoFileRecord in self.found_filesystem_video_files:
            newFullName = aLoadedFilesystemVideoFileRecord.get_full_name()
            
            if newFullName in self.finalOutputParsedVideoResultFileSources.keys():
                #This indicates that it was already found in the database
                potentially_computed_end_date = aLoadedFilesystemVideoFileRecord.get_computed_end_date()
                if (potentially_computed_end_date is not None):
                    # if we have a valid computed end_date (meaning we loaded metadata) then we say the newest is from the filesystem.
                    self.finalOutputParsedVideoResultFileSources[newFullName] = CachedFileSource.NewestFromFilesystem
                    should_add_curr_record = True
                    # should replace the one from the database
                else:
                    # otherwise we say the newest is from the database
                    self.finalOutputParsedVideoResultFileSources[newFullName] = CachedFileSource.NewestFromDatabase
                    should_add_curr_record = False
                
            else:
                #if the key is missing, it wasn't found in the database.
                self.finalOutputParsedVideoResultFileSources[newFullName] = CachedFileSource.OnlyFromFilesystem
                should_add_curr_record = True

            if (should_add_curr_record):
                # aLoadedFilesystemVideoFileRecord.set_source(self.finalOutputParsedVideoResultFileSources[newFullName])
                finalOutputParsedVideoResultFilesDict[newFullName] = aLoadedFilesystemVideoFileRecord
                # self.finalOutputParsedVideoResultFiles.append(aLoadedFilesystemVideoFileRecord)

            finalOutputParsedVideoResultFilesDict[newFullName].set_source(self.finalOutputParsedVideoResultFileSources[newFullName])

        # Build final output array:
        for (aKey, aValue) in finalOutputParsedVideoResultFilesDict.items():
            finalOutputParsedVideoResultFilesList.append(aValue)

        # Final output
        self.finalOutputParsedVideoResultFiles = sorted(finalOutputParsedVideoResultFilesList, key=lambda obj: obj.parsed_date)
            

    def get_combined_video_files(self):
        return self.finalOutputParsedVideoResultFiles


class OperationTypes(Enum):
        NoOperation = 1
        FilesystemFileFind = 2
        FilesystemMetadataLoad = 3

class PendingFilesystemOperation(QObject):

    def __init__(self, operation_type=OperationTypes.NoOperation, end_num = 0, start_num = 0, parent=None):
        super().__init__(parent=parent)
        self.operation_type = operation_type
        self.end_num = end_num
        self.start_num = 0

    def restart(self, op_type, end_num):
        self.operation_type = op_type
        self.end_num = end_num
        self.start_num = 0

    # updates with the percent value
    def update(self, new_percent):
        newVal = (float(new_percent) * float(self.end_num))
        self.start_num = newVal

    def get_fraction(self):
        if self.end_num > 0:
            return (float(self.start_num)/float(self.end_num))
        else:
            return 0.0

    def get_percent(self):
        return (self.get_fraction()*100.0)

    def is_finished(self):
        if self.end_num > 0:
            return (self.start_num == self.end_num)
        else:
            return False


## VideoFilesystemLoader: this object tries to find video files in the filesystem and add them to the database if they don't exist
"""
Loads the VideoFiles from the database (cached versions) and then tries to search the filesystem for additional video files.
"""
class VideoFilesystemLoader(AbstractDatabaseAccessingQObject):

    VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths
    # VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadOnlyFromDatabase


    foundFilesUpdated = pyqtSignal()

    findMetadataComplete = pyqtSignal()
    findVideosComplete = pyqtSignal()

    def __init__(self, database_connection, videoFileSearchPaths, parent=None):
        super(VideoFilesystemLoader, self).__init__(database_connection, parent=parent) # Call the inherited classes __init__ method
        self.cache = dict()
        self.loadedParentFolders = []
        self.loadedVideoFiles = []
        self.pending_operation_status = PendingFilesystemOperation(OperationTypes.NoOperation, 0, 0, parent=self)

        self.shouldEnableFilesystemMetadataUpdate = False

        self.searchPaths = videoFileSearchPaths
        self.reload_on_search_paths_changed()
        
        self.videoFilesystemWorker = None
        self.videoMetadataWorker = None
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.reload_data()


    def get_cache(self):
        return self.cache

    ## DATABASE Functions:
    def reload_data(self):
        print("VideoFilesystemLoader.reload_data(...)")
        # Load the video files depending on the setting.
        if VideoFilesystemLoader.VideoFileLoadingMode == CachedVideoFileLoadingOptions.LoadOnlyFromDatabase:
            print("Only loading video files from database. Ignoring search paths...")
            self.reloadModelFromDatabase()
        elif VideoFilesystemLoader.VideoFileLoadingMode == CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths:
            print("Loading video files from database and searching search paths...")
            self.reloadModelFromDatabase()
            self.find_filesystem_video()
        else:
            print("VideoFilesystemLoader ERROR: Unexpected enum type!")
            pass

        self.foundFilesUpdated.emit()


    # TODO: should build parent nodes from a combination of the loaded parents and the search paths (if we're in a mode to load search paths)
    
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        print("VideoFilesystemLoader.reloadModelFromDatabase(...)")
        # Load the latest behaviors and colors data from the database
        self.fileExtensionDict = self.database_connection.load_static_file_extensions_from_database()
        self.loadedParentFolders = self.database_connection.load_file_parent_folders_from_database(include_video_files=True)
        self.loadedVideoFiles = []
        currLoadedVideoFiles = []

        # Iterate through all found parent folders, replacing the versions in the cache with the ones from the database
        for aLoadedParentFolder in self.loadedParentFolders:

            aFinalSearchPath = aLoadedParentFolder.fullpath

            if (not (aFinalSearchPath in self.cache.keys())):
                # Parent doesn't yet exist in cache
                self.cache[aFinalSearchPath] = ParentDirectoryCache(aFinalSearchPath, CachedFileSource.OnlyFromDatabase)
            else:
                # Parent already exists
                # TODO: update parent?
                # self.cache[aFinalSearchPath].set_source()
                pass

            
            #TODO: don't replace the cache's entries in case they were loaded from the filesystem
            currLoadedVideoFiles = aLoadedParentFolder.videoFiles
            self.loadedVideoFiles.extend(currLoadedVideoFiles)
            print("currLoadedVideoFiles[{0}]: {1}".format(str(aLoadedParentFolder.fullpath), len(currLoadedVideoFiles)))
            self.cache[aLoadedParentFolder.fullpath].set_database_parent_folder_obj(aLoadedParentFolder)
            self.cache[aLoadedParentFolder.fullpath].set_database_video_files(currLoadedVideoFiles)

        self.foundFilesUpdated.emit()


    # Called to add a searcg path
    def add_search_path(self, newSearchPath):
        self.searchPaths.append(newSearchPath)
        self.reload_on_search_paths_changed()
        self.reload_data()


    def reload_on_search_paths_changed(self):
        print("VideoFilesystemLoader.reload_on_search_paths_changed(...)")
        self.reloadModelFromDatabase()
        self.rebuildParentFolders()

        self.foundFilesUpdated.emit()


    def saveVideoFilesToDatabase(self):
        print("VideoFilesystemLoader.saveVideoFilesToDatabase(...)")
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
        print("VideoFilesystemLoader.rebuildParentFolders(...)")
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



    ## Find_video_metadata:
        # Finds the video metadata in a multithreaded way
    def find_video_metadata(self):
        print("VideoFilesystemLoader.find_video_metadata(...)")
        # Pass the function to execute
        self.videoMetadataWorker = VideoMetadataWorker(self.on_find_video_metadata_execute_thread) # Any other args, kwargs are passed to the run function
        self.videoMetadataWorker.signals.result.connect(self.on_find_video_metadata_print_output)
        self.videoMetadataWorker.signals.finished.connect(self.on_find_video_metadata_thread_complete)
        self.videoMetadataWorker.signals.progress.connect(self.on_find_video_metadata_progress_fn)
        
        # Execute
        self.threadpool.start(self.videoMetadataWorker) 


    def on_find_video_metadata_progress_fn(self, n):
        self.pending_operation_status.update(n)
        print("%d%% done" % n)

    def on_find_video_metadata_execute_thread(self, progress_callback):
        currProgress = 0.0
        parsedFiles = 0
        self.pending_operation_status.restart(OperationTypes.FilesystemMetadataLoad, self.total_found_files)

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
        self.foundFilesUpdated.emit()


    ## FILESYSTEM:
    # Finds the video files in the self.searchPaths in a multithreaded way
    def find_filesystem_video(self):
        print("VideoFilesystemLoader.find_filesystem_video(...)")
        # Pass the function to execute
        self.videoFilesystemWorker = VideoFilesystemWorker(self.on_find_filesystem_video_execute_thread) # Any other args, kwargs are passed to the run function
        self.videoFilesystemWorker.signals.result.connect(self.on_find_filesystem_video_print_output)
        self.videoFilesystemWorker.signals.finished.connect(self.on_find_filesystem_video_thread_complete)
        self.videoFilesystemWorker.signals.progress.connect(self.on_find_filesystem_video_progress_fn)
        
        # Execute
        self.threadpool.start(self.videoFilesystemWorker) 


    def on_find_filesystem_video_progress_fn(self, n):
        self.pending_operation_status.update(n)
        print("%d%% done" % n)

    def on_find_filesystem_video_execute_thread(self, progress_callback):
        searchedSearchPaths = 0
        # self.found_files_lists = []
        # TODO: clear old files from cache?
        self.total_found_files = 0
        self.total_search_paths = len(self.searchPaths)
        self.pending_operation_status.restart(OperationTypes.FilesystemFileFind, self.total_search_paths)

        # Clear the top-level nodes
        for aSearchPath in self.searchPaths:
            curr_search_path_video_files = findVideoFiles(aSearchPath, shouldPrint=False)
            # self.found_files_lists.append(curr_search_path_video_files)
            self.cache[aSearchPath].set_found_filesystem_video_files(curr_search_path_video_files) ## TODO: Don't overwrite the previously cached/found video files
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
        self.rebuildParentFolders()
        self.findVideosComplete.emit()
        self.foundFilesUpdated.emit()

        # Find the metadata for all the video
        if (self.shouldEnableFilesystemMetadataUpdate):
            print("Finding metadata...")
            self.find_video_metadata()
        else:
            print("skipping metadata...")