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
from app.filesystem.VideoUtils import findDeeplabCutProducedOutputFiles, FoundDeeplabcutOutputFileResult

# from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker, VideoMetadataWorkerSignals
# from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker, VideoFilesystemWorkerSignals
from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker
from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker

from pathlib import Path

from app.database.entry_models.db_model import FileParentFolder, StaticFileExtension, VideoFile
from app.filesystem.VideoConversionHelpers import HandbrakeConversionQueue, save_handbrake_conversion_queue
from app.filesystem.FilesystemOperations import OperationTypes, PendingFilesystemOperation

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
        self.found_filesystem_data_output_files = []

        self.finalOutputParsedVideoResultFileSources = dict()
        self.finalOutputParsedVideoResultFiles = []

        self.final_output_matching_videoFileBaseName_DataFile_dict = dict() # A map from a videoFile's base name to a list of data files

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
        
    def get_found_filesystem_data_output_files(self):
        return self.found_filesystem_data_output_files

    def set_found_filesystem_deeplabcut_data_output_files(self, new_found_filesystem_dlc_data_output_files):
        self.found_filesystem_data_output_files = new_found_filesystem_dlc_data_output_files
        self.rebuild_combined_data_files()

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

        self.final_output_matching_videoFileBaseName_DataFile_dict = dict()

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

    # Called to rebuild the dictionary that maps from a video file to a data file
    def rebuild_combined_data_files(self):
        # Find matching video files for each data file
        # final_output_matching_dataFile_videoFile_dict = dict()
        self.final_output_matching_videoFileBaseName_DataFile_dict = dict()

        for aVideoFile in self.get_combined_video_files():
            currVideoFileBaseName = aVideoFile.get_base_name()
            if currVideoFileBaseName not in self.final_output_matching_videoFileBaseName_DataFile_dict.keys():
                # Create the new key with an empty list if it doesn't yet exist
                self.final_output_matching_videoFileBaseName_DataFile_dict[currVideoFileBaseName] = []
            
            for aDataFile in self.get_found_filesystem_data_output_files():
                if (currVideoFileBaseName == aDataFile.get_base_video_file_name()):
                    # Add the data file to the existing list for that key
                    self.final_output_matching_videoFileBaseName_DataFile_dict[currVideoFileBaseName].append(aDataFile)

                # if currVideoFileBaseName in final_output_matching_videoFileBaseName_DataFile_dict.keys():
                #     # Add the data file to the existing list for that key
                #     final_output_matching_videoFileBaseName_DataFile_dict[currVideoFileBaseName].append(aDataFile)
                # else:
                #     # Create the new key with a list containing just this data file
                #     final_output_matching_videoFileBaseName_DataFile_dict[currVideoFileBaseName] = [aDataFile]
                
                
    def get_combined_video_file_basenames_to_data_file_list_map(self):
        return self.final_output_matching_videoFileBaseName_DataFile_dict


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

    findFilesInSearchDirectoryComplete = pyqtSignal(str)

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
    def reload_data(self, restricted_search_paths=None):
        print("VideoFilesystemLoader.reload_data(...)")
        # Load the video files depending on the setting.
        if VideoFilesystemLoader.VideoFileLoadingMode == CachedVideoFileLoadingOptions.LoadOnlyFromDatabase:
            print("Only loading video files from database. Ignoring search paths...")
            self.reloadModelFromDatabase()
        elif VideoFilesystemLoader.VideoFileLoadingMode == CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths:
            print("Loading video files from database and searching search paths...")
            self.reloadModelFromDatabase()
            # Rebuild self.searchPaths from the database's parent folders
            self.searchPaths = [str(aSearchPath) for aSearchPath in self.cache.keys()]
            if restricted_search_paths is None:
                restricted_search_paths = self.searchPaths

            self.find_filesystem_video(restricted_search_paths)
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
                # Parent doesn't yet exist in cache, create it
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
    def find_video_metadata(self, activeSearchPaths):
        print("VideoFilesystemLoader.find_video_metadata(...)")
        # Pass the function to execute
        self.videoMetadataWorker = VideoMetadataWorker(activeSearchPaths, self.on_find_video_metadata_execute_thread) # Any other args, kwargs are passed to the run function
        self.videoMetadataWorker.signals.result.connect(self.on_find_video_metadata_print_output)
        self.videoMetadataWorker.signals.finished.connect(self.on_find_video_metadata_thread_complete)
        self.videoMetadataWorker.signals.progress.connect(self.on_find_video_metadata_progress_fn)
        
        # Execute
        self.threadpool.start(self.videoMetadataWorker) 

    @pyqtSlot(list, int)
    def on_find_video_metadata_progress_fn(self, active_search_paths, n):
        self.pending_operation_status.update(n)
        print("%d%% done" % n)

    def on_find_video_metadata_execute_thread(self, active_search_paths, progress_callback):
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
 
    @pyqtSlot(list, object)
    def on_find_video_metadata_print_output(self, active_search_paths, s):
        print(s)
        
    @pyqtSlot(list)
    def on_find_video_metadata_thread_complete(self, finished_search_paths):
        print("THREAD on_find_video_metadata_thread_complete(...)! {0}".format(str(finished_search_paths)))
        self.findMetadataComplete.emit()
        self.foundFilesUpdated.emit()


    ## FILESYSTEM:
    # Finds the video files in the self.searchPaths in a multithreaded way
    def find_filesystem_video(self, activeSearchPaths):
        print("VideoFilesystemLoader.find_filesystem_video(...):  active_search_paths: {0}".format(str(activeSearchPaths)))
        # Pass the function to execute
        
        self.videoFilesystemWorker = VideoFilesystemWorker(activeSearchPaths, self.on_find_filesystem_video_execute_thread) # Any other args, kwargs are passed to the run function
        self.videoFilesystemWorker.signals.result.connect(self.on_find_filesystem_video_print_output)
        self.videoFilesystemWorker.signals.finished.connect(self.on_find_filesystem_video_thread_complete)
        self.videoFilesystemWorker.signals.progress.connect(self.on_find_filesystem_video_progress_fn)
        
        # Execute
        self.threadpool.start(self.videoFilesystemWorker)

    @pyqtSlot(list, int)
    def on_find_filesystem_video_progress_fn(self, active_search_paths, n):
        self.pending_operation_status.update(n)
        print("%d%% done" % n)

    def on_find_filesystem_video_execute_thread(self, active_search_paths, progress_callback):
        print("THREAD on_find_filesystem_video_execute_thread(...)! active_search_paths: {0}".format(str(active_search_paths)))

        searchedSearchPaths = 0
        # self.found_files_lists = []
        # TODO: clear old files from cache?
        self.total_found_files = 0
        self.total_search_paths = len(active_search_paths)
        self.pending_operation_status.restart(OperationTypes.FilesystemFileFind, self.total_search_paths)

        # Clear the top-level nodes
        for aSearchPath in active_search_paths:
            curr_search_path_video_files = findVideoFiles(aSearchPath, shouldPrint=False)
            curr_search_path_deeplabcut_data_files = findDeeplabCutProducedOutputFiles(aSearchPath, shouldPrint=False)

            # self.found_files_lists.append(curr_search_path_video_files)
            self.cache[aSearchPath].set_found_filesystem_video_files(curr_search_path_video_files) ## TODO: Don't overwrite the previously cached/found video files
            self.cache[aSearchPath].set_found_filesystem_deeplabcut_data_output_files(curr_search_path_deeplabcut_data_files)
            self.total_found_files = self.total_found_files + len(curr_search_path_video_files)
            searchedSearchPaths = searchedSearchPaths + 1
            self.findFilesInSearchDirectoryComplete.emit(aSearchPath)
            progress_callback.emit(active_search_paths, (searchedSearchPaths*100/self.total_search_paths))

        return "Done."
 
    @pyqtSlot(list, object)
    def on_find_filesystem_video_print_output(self, active_search_paths, s):
        print(s)
        
    @pyqtSlot(list)
    def on_find_filesystem_video_thread_complete(self, finished_search_paths):
        print("THREAD on_find_filesystem_video_thread_complete(...)! {0}".format(str(finished_search_paths)))
        
        # Returned results in self.found_files_lists
        # self.rebuild_from_found_files()
        self.rebuildParentFolders()
        self.findVideosComplete.emit()
        self.foundFilesUpdated.emit()

        # Find the metadata for all the video
        if (self.shouldEnableFilesystemMetadataUpdate):
            print("Finding metadata...")
            self.find_video_metadata(finished_search_paths)
        else:
            print("skipping metadata...")