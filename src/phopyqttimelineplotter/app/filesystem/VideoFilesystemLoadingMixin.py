# VideoFilesystemLoadingMixin.py
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from app.database.entry_models.db_model import (
    FileParentFolder,
    StaticFileExtension,
    VideoFile,
)
from app.filesystem.FilesystemOperations import (
    OperationTypes,
    PendingFilesystemOperation,
)
from app.filesystem.VideoConversionHelpers import (
    HandbrakeConversionQueue,
    save_handbrake_conversion_queue,
)
from app.filesystem.VideoUtils import (
    CachedFileSource,
    FoundDeeplabcutOutputFileResult,
    FoundVideoFileResult,
    VideoParsedResults,
    findDeeplabCutProducedOutputFiles,
    findVideoFiles,
)
from app.filesystem.Workers.FileMetadataWorkers import FileMetadataWorker
from app.filesystem.Workers.VideoFilesystemWorkers import VideoFilesystemWorker
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import (
    QDir,
    QEvent,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QThreadPool,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QFileSystemModel,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QTreeView,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    qApp,
)

from phopyqttimelineplotter.GUI.UI.AbstractDatabaseAccessingWidgets import (
    AbstractDatabaseAccessingQObject,
)

# from app.filesystem.VideoFilesystemLoadingMixin import CachedVideoFileLoadingOptions, ParentDirectoryCache, VideoFilesystemLoader


class CachedVideoFileLoadingOptions(Enum):
    LoadOnlyFromDatabase = 1  # Only loads the video file records from the sqlite database. Doesn't search the disk for new video files or update existing ones
    LoadDatabaseAndSearchVideoFileSearchPaths = 2  #  Load the video file records from the sqlite database AND search the video file search paths for new or updated video files.


class CachedDataFileLoadingOptions(Enum):
    LoadOnlyFromDatabase = 1  # Only loads the video file records from the sqlite database. Doesn't search the disk for new video files or update existing ones
    LoadDatabaseAndSearchVideoFileSearchPaths = 2  #  Load the video file records from the sqlite database AND search the video file search paths for new or updated video files.


# Represents an abstract "ParentDirectory", which is a collection of video files grouped by the user.
# In the filesystem hierarchy, this represents a behaviora box specific folder such as "Transcoded Videos/BB02/" containing videos.
# The files in this folder are added to the database when they're found and parsed, meaning information about them can exist either:
# 1. Only in the database
# 2. Only in the filesystem
# 3. Both in the filesystem and the database
# This cache aims to return a unique list of video files, meaning only including one copy of each file (even if it's represented both in the filesystem and database)
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

        self.final_output_matching_videoFileBaseName_DataFile_dict = (
            dict()
        )  # A map from a videoFile's base name to a list of data files

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

    # Sets the filesystem versions of the video files and intellegently rebuilds the combined video files.
    def set_found_filesystem_video_files(self, new_found_filesystem_video_files):
        self.found_filesystem_video_files = new_found_filesystem_video_files
        self.rebuild_combined_video_files()

    def get_found_filesystem_data_output_files(self):
        return self.found_filesystem_data_output_files

    def set_found_filesystem_deeplabcut_data_output_files(
        self, new_found_filesystem_dlc_data_output_files
    ):
        self.found_filesystem_data_output_files = (
            new_found_filesystem_dlc_data_output_files
        )
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
                print(
                    "ERROR: this should be impossible! We just cleared the finalOutputParsedVideoResultFileSources!"
                )
                pass
            else:
                self.finalOutputParsedVideoResultFileSources[
                    newFullName
                ] = CachedFileSource.OnlyFromDatabase
                newObj.set_source(
                    self.finalOutputParsedVideoResultFileSources[newFullName]
                )
                finalOutputParsedVideoResultFilesDict[newFullName] = newObj

            # self.finalOutputParsedVideoResultFiles.append(newObj)

        should_add_curr_record = False

        # Filesystem:
        for aLoadedFilesystemVideoFileRecord in self.found_filesystem_video_files:
            newFullName = aLoadedFilesystemVideoFileRecord.get_full_name()

            if newFullName in self.finalOutputParsedVideoResultFileSources.keys():
                # This indicates that it was already found in the database
                potentially_computed_end_date = (
                    aLoadedFilesystemVideoFileRecord.get_computed_end_date()
                )
                if potentially_computed_end_date is not None:
                    # if we have a valid computed end_date (meaning we loaded metadata) then we say the newest is from the filesystem.
                    self.finalOutputParsedVideoResultFileSources[
                        newFullName
                    ] = CachedFileSource.NewestFromFilesystem
                    should_add_curr_record = True
                    # should replace the one from the database
                else:
                    # otherwise we say the newest is from the database and use the database version
                    self.finalOutputParsedVideoResultFileSources[
                        newFullName
                    ] = CachedFileSource.NewestFromDatabase
                    should_add_curr_record = False  # don't set the dict entry to the filesystem version, keep the database version that was already set.

            else:
                # if the key is missing, it wasn't found in the database.
                self.finalOutputParsedVideoResultFileSources[
                    newFullName
                ] = CachedFileSource.OnlyFromFilesystem
                should_add_curr_record = True

            if should_add_curr_record:
                # aLoadedFilesystemVideoFileRecord.set_source(self.finalOutputParsedVideoResultFileSources[newFullName])
                finalOutputParsedVideoResultFilesDict[
                    newFullName
                ] = aLoadedFilesystemVideoFileRecord
                # self.finalOutputParsedVideoResultFiles.append(aLoadedFilesystemVideoFileRecord)

            finalOutputParsedVideoResultFilesDict[newFullName].set_source(
                self.finalOutputParsedVideoResultFileSources[newFullName]
            )

        # Build final output array:
        for (aKey, aValue) in finalOutputParsedVideoResultFilesDict.items():
            finalOutputParsedVideoResultFilesList.append(aValue)

        # Final output
        self.finalOutputParsedVideoResultFiles = sorted(
            finalOutputParsedVideoResultFilesList, key=lambda obj: obj.parsed_date
        )

    # Simple Getter to the combined_video_files function
    def get_combined_video_files(self):
        return self.finalOutputParsedVideoResultFiles

    # Called to rebuild the dictionary that maps from a video file to a data file
    def rebuild_combined_data_files(self):
        # Find matching video files for each data file
        # final_output_matching_dataFile_videoFile_dict = dict()
        self.final_output_matching_videoFileBaseName_DataFile_dict = dict()

        for aVideoFile in self.get_combined_video_files():
            currVideoFileBaseName = aVideoFile.get_base_name()
            if (
                currVideoFileBaseName
                not in self.final_output_matching_videoFileBaseName_DataFile_dict.keys()
            ):
                # Create the new key with an empty list if it doesn't yet exist
                self.final_output_matching_videoFileBaseName_DataFile_dict[
                    currVideoFileBaseName
                ] = []

            for aDataFile in self.get_found_filesystem_data_output_files():
                if currVideoFileBaseName == aDataFile.get_base_video_file_name():
                    # Add the data file to the existing list for that key
                    self.final_output_matching_videoFileBaseName_DataFile_dict[
                        currVideoFileBaseName
                    ].append(aDataFile)

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

    VideoFileLoadingMode = (
        CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths
    )
    # VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadOnlyFromDatabase
    DataFileLoadingMode = (
        CachedDataFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths
    )

    foundFilesUpdated = pyqtSignal()

    findMetadataComplete = pyqtSignal()
    findVideosComplete = pyqtSignal()

    findFilesInSearchDirectoryComplete = pyqtSignal(str)

    def __init__(self, database_connection, videoFileSearchPaths, parent=None):
        super(VideoFilesystemLoader, self).__init__(
            database_connection, parent=parent
        )  # Call the inherited classes __init__ method

        # self.cache: a dictionary index by file search paths, with ParentDirectoryCache-type values.
        self.cache = dict()
        self.loadedParentFolders = []
        # self.loadedVideoFiles = []
        self.pending_operation_status = PendingFilesystemOperation(
            OperationTypes.NoOperation, 0, 0, parent=self
        )

        self.shouldEnableFilesystemMetadataUpdate = True

        self.searchPaths = videoFileSearchPaths
        self.reload_on_search_paths_changed()

        self.videoFilesystemWorker = None
        self.videoMetadataWorker = None
        self.threadpool = QThreadPool()
        print(
            "Multithreading with maximum %d threads" % self.threadpool.maxThreadCount()
        )
        self.reload_data()

    def get_cache(self):
        return self.cache

    # reload_data(...): reloads all data from the database (and if the options permit, the filesystem self.searchPaths)
    # NOTE: overwrites self.searchPaths
    def reload_data(self, restricted_search_paths=None):
        print("VideoFilesystemLoader.reload_data(...)")
        # Load the video files depending on the setting.
        if (
            VideoFilesystemLoader.VideoFileLoadingMode
            == CachedVideoFileLoadingOptions.LoadOnlyFromDatabase
        ):
            print("Only loading video files from database. Ignoring search paths...")
        else:
            print("Loading video files from database...")

        # Load from the database (which is done in both modes:
        self.reloadModelFromDatabase()

        # Rebuild self.searchPaths from the database's parent folders
        self.searchPaths = [str(aSearchPath) for aSearchPath in self.cache.keys()]
        if restricted_search_paths is None:
            restricted_search_paths = self.searchPaths

        if (
            VideoFilesystemLoader.VideoFileLoadingMode
            == CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths
        ):
            print(
                "Loading video files from search paths: {}...".format(self.searchPaths)
            )
            self.find_filesystem_video(
                restricted_search_paths
            )  # Load the videos from the restricted search paths.

        self.foundFilesUpdated.emit()  # This returns before the filesystem search is finished, but is used to update the UI to indicate that it's searching.

    # TODO: should build parent nodes from a combination of the loaded parents and the search paths (if we're in a mode to load search paths)

    ## DATABASE Functions:
    # Updates the member variables from the database
    # Updates self.cache[*] entries for each parent_folder loaded from the database (by calling set_database_video_files and set_database_parent_folder_obj on them), creating new ParentDirectoryCache if needed.
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        print("VideoFilesystemLoader.reloadModelFromDatabase(...)")
        # Load the latest behaviors and colors data from the database
        self.fileExtensionDict = (
            self.database_connection.load_static_file_extensions_from_database()
        )
        self.loadedParentFolders = (
            self.database_connection.load_file_parent_folders_from_database(
                include_video_files=True
            )
        )
        # self.loadedVideoFiles = []
        currDatabaseLoadedVideoFiles = []

        # Iterate through all found parent folders, replacing the versions in the cache with the ones from the database
        for aLoadedParentFolder in self.loadedParentFolders:

            aFinalSearchPath = aLoadedParentFolder.fullpath

            if not (aFinalSearchPath in self.cache.keys()):
                # Parent doesn't yet exist in cache, create it
                self.cache[aFinalSearchPath] = ParentDirectoryCache(
                    aFinalSearchPath, CachedFileSource.OnlyFromDatabase
                )
            else:
                # Parent already exists
                # TODO: I believe I should check and see if the self.cache[aFinalSearchPath] is CachedFileSource.OnlyFromFilesystem, and if so, update it to indicate that it's also in the database.
                # TODO: update parent?
                # self.cache[aFinalSearchPath].set_source()
                pass

            # currLoadedVideoFiles are the video files from the database
            currDatabaseLoadedVideoFiles = (
                aLoadedParentFolder.videoFiles
            )  # Database video files
            # self.loadedVideoFiles.extend(currLoadedVideoFiles)
            print(
                "currDatabaseLoadedVideoFiles[{0}]: {1}".format(
                    str(aLoadedParentFolder.fullpath), len(currDatabaseLoadedVideoFiles)
                )
            )
            self.cache[aLoadedParentFolder.fullpath].set_database_parent_folder_obj(
                aLoadedParentFolder
            )
            self.cache[aLoadedParentFolder.fullpath].set_database_video_files(
                currDatabaseLoadedVideoFiles
            )  # Intellegently builds the combined files

        self.foundFilesUpdated.emit()

    # Called to add a searcg path
    def add_search_path(self, newSearchPath):
        if newSearchPath in self.searchPaths:
            # Already exists in the search paths. Don't add it. Are the search paths updated from the database objects?
            print(
                "Search path {} already exists in self.searchPaths. Will searching it again for video files.".format(
                    newSearchPath
                )
            )
            pass
        else:
            print(
                "Adding new search path: {} to self.searchPaths".format(newSearchPath)
            )
            self.searchPaths.append(newSearchPath)  # Add it to the search path array
            self.reload_on_search_paths_changed()  # Doesn't update self.searchPaths or use the new search path. This is done to ensure that the cache has the latest entries from the database (in case the database changes during program operation?)

        # self.reload_data() is called with freshly updated self.cache dict entries and new database parent entries for each search path
        self.reload_data()

    # Called when self.searchPaths is updated to add DatabaseDirectoryCache entries to the cache for new searchPaths if needed.
    def reload_on_search_paths_changed(self):
        print("VideoFilesystemLoader.reload_on_search_paths_changed(...)")
        self.reloadModelFromDatabase()  # This is needed to update self.loadedParentFolders, which is used in rebuildDatabaseRecordParentFolders() to check if the entry is in the database
        self.rebuildDatabaseRecordParentFolders()

        self.foundFilesUpdated.emit()  # note that no files are updated at this point, but I think this is called to refresh the filesystem UI tree to indicate that it's try to find files in these dirs.

    def saveVideoFilesToDatabase(self):
        print("VideoFilesystemLoader.saveVideoFilesToDatabase(...)")
        # TODO: should we reload the cache again from database? Prob not needed.
        for (key_path, cache_value) in self.cache.items():
            loaded_parent_folder_obj = cache_value.get_database_parent_folder()
            curr_filesystem_search_path_video_files = (
                cache_value.get_filesystem_video_files()
            )
            existing_database_video_files = (
                cache_value.get_database_video_files()
            )  # Get cached database files

            # Loop through all found filesystem video files to see if any need new records to be created in the database
            for aFoundVideoFile in curr_filesystem_search_path_video_files:
                # Get the appropriate file extension parent
                currFileExtension = aFoundVideoFile.file_extension[1:].lower()
                parent_file_extension_obj = None
                if currFileExtension in self.fileExtensionDict.keys():
                    parent_file_extension_obj = self.fileExtensionDict[
                        currFileExtension
                    ]
                else:
                    # Key doesn't exist!
                    print(
                        "Video File extension {0} doesn't exist in database! Adding it and saving.".format(
                            currFileExtension
                        )
                    )
                    parent_file_extension_obj = StaticFileExtension(currFileExtension)
                    # Add it to the database
                    self.database_connection.save_static_file_extensions_to_database(
                        [parent_file_extension_obj]
                    )

                # What is this? Also, should we only save video files with properly computed end dates? Should we update those that didn't have computed end dates, but do now?
                potentially_computed_end_date = aFoundVideoFile.get_computed_end_date()
                if potentially_computed_end_date:
                    computed_end_date = str(potentially_computed_end_date)
                else:
                    computed_end_date = "Loading..."

                # Check if the videoFile exists:
                need_create_new_video_file = True
                for anExistingVideoFile in existing_database_video_files:
                    if anExistingVideoFile.file_fullname == aFoundVideoFile.full_name:
                        # print("File already exists, skipping...")
                        need_create_new_video_file = False
                        break
                    else:
                        continue

                if need_create_new_video_file:
                    # Create the video file if needed

                    aNewVideoFileRecord = VideoFile.from_parsed_video_result_obj(
                        aFoundVideoFile, None, None, None, "auto"
                    )
                    # aNewVideoFileRecord = aFoundVideoFile.get_database_videoFile_record(None,None,None,'auto')
                    aNewVideoFileRecord.staticFileExtension = parent_file_extension_obj
                    aNewVideoFileRecord.fileParentFolder = loaded_parent_folder_obj

                    # Add the video file record
                    self.database_connection.save_video_file_info_to_database(
                        [aNewVideoFileRecord]
                    )

    # rebuildDatabaseRecordParentFolders(): iterates through self.searchPaths and performs the following operations:
    # 1. Creates new ParentDirectoryCache entries in self.cache[aFinalSearchPath] if they don't already exist.
    # 2. Creates new "FileParentFolder" entries in the database from self.searchPaths if existing ones can't be found
    def rebuildDatabaseRecordParentFolders(self):
        print("VideoFilesystemLoader.rebuildParentFolders(...)")
        unresolvedSearchPaths = self.searchPaths
        # self.searchPathsParentIDs = []

        # Iterate through all searchPaths in self.searchPaths.
        for (index, aSearchPath) in enumerate(unresolvedSearchPaths):
            currPath = Path(aSearchPath).resolve()
            currRootAnchor = currPath.anchor
            currRemainder = currPath.relative_to(currRootAnchor)
            print(
                "currPath: {0}; currRootAnchor: {1}; currRemainder: {2}".format(
                    currPath, currRootAnchor, currRemainder
                )
            )

            aFinalSearchPath = str(currPath)
            self.searchPaths[index] = aFinalSearchPath

            # Adds it to the cache if it isn't alread there.
            if not (aFinalSearchPath in self.cache.keys()):
                # Parent doesn't yet exist in cache, create it
                self.cache[aFinalSearchPath] = ParentDirectoryCache(aFinalSearchPath)
            else:
                # Parent already exists at self.cache[aFinalSearchPath]
                pass

            # Iterate through all loaded parents to see if the parent already exists
            finalParent = None

            # Database folders
            for aParentFolder in self.loadedParentFolders:
                aParentPath = Path(aParentFolder.fullpath).resolve()
                # Try to match to the loaded parent objects from the database
                if aParentPath.samefile(currPath):
                    # currPath is the same file as the loaded parent path
                    print("Found existing parent for {0}".format(currPath))
                    finalParent = aParentFolder
                    break  # Exit the loop because we found a match.

            # If we get through all loaded parents and the parent doesn't already exist, create the database FileParentFolder record and persist it to the database.
            if finalParent is None:
                print(
                    "Creating new FileParentFolder record in the database: {0}".format(
                        currPath
                    )
                )
                finalParent = FileParentFolder(
                    None, currPath, currRootAnchor, currRemainder, "auto"
                )
                # Save parent to database
                self.database_connection.save_file_parent_folders_to_database(
                    [finalParent]
                )
                # Set parent to the newly created database parent object in the cache
                self.cache[aFinalSearchPath].set_database_parent_folder_obj(finalParent)
                # Add the newly created object to the local array of database loaded parents:
                self.loadedParentFolders.append(finalParent)

            # What's the point of the code below? A separate check?
            if finalParent is None:
                print("Still nONE!")
                # self.searchPathsParentIDs.append(None)
                self.cache[aFinalSearchPath].set_database_parent_folder_obj(None)
            else:
                print("     parent id: {0}".format(finalParent.id))
                # self.searchPathsParentIDs.append(finalParent.id)
                self.cache[aFinalSearchPath].set_database_parent_folder_obj(finalParent)

    ## Primary Filesystem Functions

    ##
    #### FILESYSTEM: VIDEOS METADATA THREADING FUNCTIONS:

    ## Find_video_metadata:
    # Finds the video metadata in a multithreaded way
    def find_video_metadata(self, activeSearchPaths):
        print("VideoFilesystemLoader.find_video_metadata(...)")
        # Pass the function to execute
        self.videoMetadataWorker = FileMetadataWorker(
            activeSearchPaths, self.on_find_video_metadata_execute_thread
        )  # Any other args, kwargs are passed to the run function
        self.videoMetadataWorker.signals.result.connect(
            self.on_find_video_metadata_print_output
        )
        self.videoMetadataWorker.signals.finished.connect(
            self.on_find_video_metadata_thread_complete
        )
        self.videoMetadataWorker.signals.progress.connect(
            self.on_find_video_metadata_progress_fn
        )

        # Execute
        self.threadpool.start(self.videoMetadataWorker)

    @pyqtSlot(list, int)
    def on_find_video_metadata_progress_fn(self, active_search_paths, n):
        self.pending_operation_status.update(n)
        print("%d%% done" % n)

    def on_find_video_metadata_execute_thread(
        self, active_search_paths, progress_callback
    ):
        currProgress = 0.0
        parsedFiles = 0
        self.pending_operation_status.restart(
            OperationTypes.FilesystemMetadataLoad, self.total_found_files
        )

        for (key_path, cache_value) in self.cache.items():
            # Iterate through all found file-lists
            for (sub_index, aFoundVideoFile) in enumerate(
                cache_value.get_filesystem_video_files()
            ):
                # Iterate through all found video-files in a given list
                aFoundVideoFile.parse()
                parsedFiles = parsedFiles + 1
                progress_callback.emit(parsedFiles * 100 / self.total_found_files)

        return "Done."

    @pyqtSlot(list, object)
    def on_find_video_metadata_print_output(self, active_search_paths, s):
        print(s)

    @pyqtSlot(list)
    def on_find_video_metadata_thread_complete(self, finished_search_paths):
        print(
            "THREAD on_find_video_metadata_thread_complete(...)! {0}".format(
                str(finished_search_paths)
            )
        )
        self.findMetadataComplete.emit()
        self.foundFilesUpdated.emit()

    ##
    #### FILESYSTEM: FIND VIDEOS THREADING FUNCTIONS:

    # Finds the video files in the self.searchPaths in a multithreaded way
    def find_filesystem_video(self, activeSearchPaths):
        print(
            "VideoFilesystemLoader.find_filesystem_video(...):  active_search_paths: {0}".format(
                str(activeSearchPaths)
            )
        )
        # Pass the function to execute

        self.videoFilesystemWorker = VideoFilesystemWorker(
            activeSearchPaths, self.on_find_filesystem_video_execute_thread
        )  # Any other args, kwargs are passed to the run function
        self.videoFilesystemWorker.signals.result.connect(
            self.on_find_filesystem_video_print_output
        )
        self.videoFilesystemWorker.signals.finished.connect(
            self.on_find_filesystem_video_thread_complete
        )
        self.videoFilesystemWorker.signals.progress.connect(
            self.on_find_filesystem_video_progress_fn
        )

        # Execute
        self.threadpool.start(self.videoFilesystemWorker)

    @pyqtSlot(list, int)
    def on_find_filesystem_video_progress_fn(self, active_search_paths, n):
        self.pending_operation_status.update(n)
        print("%d%% done" % n)

    def on_find_filesystem_video_execute_thread(
        self, active_search_paths, progress_callback
    ):
        print(
            "THREAD on_find_filesystem_video_execute_thread(...)! active_search_paths: {0}".format(
                str(active_search_paths)
            )
        )

        searchedSearchPaths = 0
        # self.found_files_lists = []
        # TODO: clear old files from cache?
        self.total_found_files = 0
        self.total_search_paths = len(active_search_paths)
        self.pending_operation_status.restart(
            OperationTypes.FilesystemFileFind, self.total_search_paths
        )

        # Clear the top-level nodes
        for aSearchPath in active_search_paths:

            if (
                VideoFilesystemLoader.VideoFileLoadingMode
                == CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths
            ):
                curr_search_path_video_files = findVideoFiles(
                    aSearchPath, shouldPrint=False
                )
                self.cache[aSearchPath].set_found_filesystem_video_files(
                    curr_search_path_video_files
                )  # Intellegently updates the cached/found video files
                self.total_found_files = self.total_found_files + len(
                    curr_search_path_video_files
                )

            if (
                VideoFilesystemLoader.DataFileLoadingMode
                == CachedDataFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths
            ):
                curr_search_path_deeplabcut_data_files = (
                    findDeeplabCutProducedOutputFiles(aSearchPath, shouldPrint=False)
                )
                self.cache[
                    aSearchPath
                ].set_found_filesystem_deeplabcut_data_output_files(
                    curr_search_path_deeplabcut_data_files
                )
                self.total_found_files = self.total_found_files + len(
                    curr_search_path_deeplabcut_data_files
                )

            searchedSearchPaths = searchedSearchPaths + 1
            self.findFilesInSearchDirectoryComplete.emit(aSearchPath)
            progress_callback.emit(
                active_search_paths,
                (searchedSearchPaths * 100 / self.total_search_paths),
            )

        return "Done."

    @pyqtSlot(list, object)
    def on_find_filesystem_video_print_output(self, active_search_paths, s):
        print(s)

    @pyqtSlot(list)
    def on_find_filesystem_video_thread_complete(self, finished_search_paths):
        print(
            "THREAD on_find_filesystem_video_thread_complete(...)! {0}".format(
                str(finished_search_paths)
            )
        )

        # Returned results in self.found_files_lists
        # self.rebuild_from_found_files()
        self.rebuildDatabaseRecordParentFolders()
        self.findVideosComplete.emit()
        self.foundFilesUpdated.emit()

        # Find the metadata for all the video
        if self.shouldEnableFilesystemMetadataUpdate:
            print("Finding metadata...")
            self.find_video_metadata(finished_search_paths)
        else:
            print("skipping metadata...")
