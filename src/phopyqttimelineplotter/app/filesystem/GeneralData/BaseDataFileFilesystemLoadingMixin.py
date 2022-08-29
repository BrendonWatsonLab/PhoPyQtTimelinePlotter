# BaseDataFileFilesystemLoadingMixin.py
# This is an attempt to generalize the data file loading functionality that's present in VideoFilesystemLoadingMixin and LabjackFilesystemLoadingMixin
import sys
# import pickle
# import cPickle
from datetime import datetime, timezone, timedelta
from enum import Enum
import numpy as np
import pandas as pd

import matplotlib.colors as mcolors

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingQObject

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult, CachedFileSource
from app.filesystem.Workers.FileMetadataWorkers import FileMetadataWorker
from app.filesystem.Workers.VideoFilesystemWorkers import VideoFilesystemWorker

from pathlib import Path

from GUI.Model.ModelViewContainer import ModelViewContainer
from app.filesystem.FilesystemOperations import OperationTypes, PendingFilesystemOperation
# from app.filesystem.BaseDataEventsLoader import BaseDataEventsLoader, PhoServerFormatArgs

from app.filesystem.FilesystemRecordBase import FilesystemRecordBase, FilesystemDataEvent_Record
from GUI.Model.Events.PhoDurationEvent import PhoDurationEvent

# from app.filesystem.BaseDataFilesystemLoadingMixin import BaseDataEventFile, BaseDataFilesystemLoader


""" BaseDataEventFile: a single imported data file containing one or more BaseData events.

"""
class BaseDataEventFile(QObject):
    def __init__(self, filePath, parent=None):
        super().__init__(parent=parent)
        self.filePath = filePath
        self.dateTimes = []
        self.variableData = []

        self.dataContainerEvents = []
        # self.dataEvents = []

        self.phoServerFormatArgs = None

    def get_file_path(self):
        return self.filePath

    def get_dateTimes(self):
        return self.dateTimes

    def get_variable_data(self):
        return self.variableData

    # def get_events(self):
    #     return self.dataEvents

    def get_container_events(self):
        return self.dataContainerEvents


    def get_parsed_dict(self):
        if self.phoServerFormatArgs is None:
            return None
        else:
            return self.phoServerFormatArgs.parsedFileInfoDict

    def set_loaded_values(self, dateTimes, variableData, dataEventsContainerArray, phoServerFormatArgs):
        self.dateTimes = dateTimes
        # self.onesEventFormatDataArray = onesEventFormatDataArray
        self.variableData = variableData
        # self.dataEvents = dataEvents
        self.dataContainerEvents = dataEventsContainerArray
        self.phoServerFormatArgs = phoServerFormatArgs


## BaseDataFilesystemLoader: this object tries to find BaseData-exported data files in the filesystem and make them accessible in memory
"""
Loads the BaseData event files
"""
class BaseDataFilesystemLoader(QObject):

    # foundFilesUpdated = pyqtSignal()
    targetDataFilePathsUpdated = pyqtSignal()

    dataFileLoaded = pyqtSignal()
    loadingDataFilesComplete = pyqtSignal()


    def __init__(self, dataFilePaths, parent=None):
        super(BaseDataFilesystemLoader, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.cache = dict()
        self.dataFilePaths = dataFilePaths

        self.loadedDataFiles = []
        self.pending_operation_status = PendingFilesystemOperation(OperationTypes.NoOperation, 0, 0, parent=self)
        self.videoStartDates = []
        self.videoEndDates = []

        self.dataFilesystemWorker = None
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(2)
        
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        
        self.reload_on_paths_changed()
        
        self.reload_data()


    def get_cache(self):
        return self.cache

    # Called to add a new path
    def add_file_path(self, newBaseDataFilePath):
        if (newBaseDataFilePath in self.dataFilePaths):
            print("WARNING: {0} is already in dataFilePaths! Not adding again.".format(str(newBaseDataFilePath)))
            return False
        
        # If it's in the array of already completed video files, skip it as well
        if (newBaseDataFilePath in self.loadedDataFiles):
            print("WARNING: {0} is already in loadedBaseDataFiles! It's already been processed, so we're not adding it again.".format(str(newBaseDataFilePath)))
            return False

        # Otherwise we can add it
        self.dataFilePaths.append(newBaseDataFilePath)
        self.reload_on_paths_changed()

    def reload_on_paths_changed(self):
        print("BaseDataFilesystemLoader.reload_on_paths_changed(...)")
        if (len(self.dataFilePaths)>0):
            self.load_data_files(self.dataFilePaths)
    
        self.targetDataFilePathsUpdated.emit()

    def reload_data(self, restricted_file_paths=None):
        print("BaseDataFilesystemLoader.reload_data(...)")
        if restricted_file_paths is None:
            restricted_file_paths = self.dataFilePaths

        if (len(restricted_file_paths)>0):
            self.load_data_files(restricted_file_paths)

        self.targetDataFilePathsUpdated.emit()

    # # TODO: Integrate with the cache
    # def loadBaseDataFile(self, aBaseDataFilePath, videoStartDates, videoEndDates):
    #     print("BaseDataFilesystemLoader.loadBaseDataFile({0})".format(str(aBaseDataFilePath)))
    #     outEventFileObj = BaseDataEventFile(aBaseDataFilePath)
    #     (dateTimes, onesEventFormatDataArray, variableData, dataEvents) = BaseDataFilesystemLoader.loadBaseDataFiles(aBaseDataFilePath, videoStartDates, videoEndDates, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
    #     outEventFileObj.set_loaded_values(dateTimes, onesEventFormatDataArray, variableData, dataEvents)
    #     # Return the created object
    #     return outEventFileObj

    # The main function that starts the threads.
    def load_data_files(self, dataFilePaths):
        print("BaseDataFilesystemLoader.load_data_files(dataFilePaths: {0})".format(str(dataFilePaths)))
        # Pass the function to execute
        self.dataFilesystemWorker = FileMetadataWorker(dataFilePaths, self.on_load_data_files_execute_thread) # Any other args, kwargs are passed to the run function
        self.dataFilesystemWorker.signals.result.connect(self.on_load_data_files_print_output)
        self.dataFilesystemWorker.signals.finished.connect(self.on_load_data_files_thread_complete)
        self.dataFilesystemWorker.signals.progress.connect(self.on_load_data_files_progress_fn)
        
        # Execute
        self.threadpool.start(self.dataFilesystemWorker) 


    ## Threads:
    # @pyqtSlot(list, int)
    # def on_load_data_files_progress_fn(self, active_data_file_paths, n):     
    #     self.pending_operation_status.update(n)
    #     self.dataDataFileLoaded.emit()
    #     print("%d%% done" % n)

    @pyqtSlot(list, int)
    def on_load_data_files_progress_fn(self, latest_file_result_list, n):
        aFoundBaseDataDataFile = latest_file_result_list[0] # The last loaded URL
        outEventFileObj = latest_file_result_list[1] # outEventFileObj: BaseDataEventFile type object
        print('on_load_data_files_progress_fn(..., n: {}): file: {}'.format(str(n), str(aFoundBaseDataDataFile)))

        # Update our cache
        if (not (aFoundBaseDataDataFile in self.cache.keys())):
            print('Creating new cache entry for {}...'.format(str(aFoundBaseDataDataFile)))
            # Parent doesn't yet exist in cache
            self.cache[aFoundBaseDataDataFile] = outEventFileObj
        else:
            # Parent already exists
            print("WARNING: data file path {} already exists in the cache. Updating its values...".format(str(aFoundBaseDataDataFile)))
            self.cache[aFoundBaseDataDataFile] = outEventFileObj
            pass

        # Add the current video file path to the loaded files
        self.loadedDataFiles.append(aFoundBaseDataDataFile)
        
        # updated!
        self.pending_operation_status.update(n)
        self.dataFileLoaded.emit()



    """
    The main execution function
    Must be overriden by specific file types to perform the loading action
    """
    def on_load_data_files_execute_thread(self, active_data_file_paths, progress_callback):

        should_filter_for_invalid_events = True
        # should_filter_for_invalid_events = False
        
        currProgress = 0.0
        parsedFiles = 0
        numPendingFiles = len(active_data_file_paths)
        self.pending_operation_status.restart(OperationTypes.FilesystemBaseDataFileLoad, numPendingFiles)

        new_cache = dict()
        
        # active_cache = self.cache
        active_cache = new_cache
        # Loop through all the data data file paths and parse the files into a BaseDataEventFile object.
        for (sub_index, aFoundBaseDataDataFile) in enumerate(active_data_file_paths):

            # BaseDataEventFile: this serves as a container to hold the loaded events
            outEventFileObj = BaseDataEventFile(aFoundBaseDataDataFile)

            # Call the static "loadBaseDataEventsFile(...) function:
            (dateTimes, dataEventContainers, phoServerFormatArgs) = BaseDataFilesystemLoader.loadBaseDataEventsFile(aFoundBaseDataDataFile, self.videoStartDates, self.videoEndDates, shouldLimitEventsToVideoDates=False, usePhoServerFormat=True, phoServerFormatIsStdOut=False, should_filter_for_invalid_events=should_filter_for_invalid_events)

            print('Loading complete... setting loaded values')
            # Cache the loaded values into the BaseDataEventFile object.
            outEventFileObj.set_loaded_values(dateTimes, [], dataEventContainers, None)
            print('done updating cache...')
            
            if (not (aFoundBaseDataDataFile in active_cache.keys())):
                # print('Creating new cache entry for {}...'.format(str(aFoundBaseDataDataFile)))
                # Parent doesn't yet exist in cache
                active_cache[aFoundBaseDataDataFile] = outEventFileObj
            else:
                # Parent already exists
                print("WARNING: data file path {} already exists in the temporary cache. Updating its values...".format(str(aFoundBaseDataDataFile)))
                active_cache[aFoundBaseDataDataFile] = outEventFileObj
                pass

            parsedFiles = parsedFiles + 1
            # progress_callback.emit(active_data_file_paths, (parsedFiles*100/numPendingFiles))
            progress_callback.emit([aFoundBaseDataDataFile, outEventFileObj], (parsedFiles*100/numPendingFiles))

        # return "Done."
        # Returns the cache when done
        return new_cache
 
    @pyqtSlot(list, object)
    def on_load_data_files_print_output(self, active_video_paths, s):
        print(s)
        
    @pyqtSlot(list)
    def on_load_data_files_thread_complete(self, finished_loaded_data_files):
        print("THREAD on_load_data_files_thread_complete(...)! {0}".format(str(finished_loaded_data_files)))
        # The finished_loaded_data_files are paths that have already been added to self.loadedBaseDataFiles. We just need to remove them from self.dataFilePaths
        for aFinishedVideoFilePath in finished_loaded_data_files:
            self.dataFilePaths.remove(aFinishedVideoFilePath)

        self.loadingDataFilesComplete.emit()






    @pyqtSlot(datetime, datetime)
    def set_start_end_video_file_dates(self, new_start_dates, new_end_dates):
        self.videoStartDates = np.array(new_start_dates)
        self.videoEndDates = np.array(new_end_dates)
        self.reload_on_paths_changed()


    @pyqtSlot(datetime, datetime, timedelta)
    def on_active_global_timeline_times_changed(self, totalStartTime, totalEndTime, totalDuration):
        # print("ReferenceMarkerManager.on_active_global_timeline_times_changed({0}, {1}, {2})".format(str(totalStartTime), str(totalEndTime), str(totalDuration)))
        # self.totalStartTime = totalStartTime
        # self.totalEndTime = totalEndTime
        # self.totalDuration = totalDuration
        return


    ## Static Methods:


    """ loadBaseDataEventsFile(...): new.
        dataEventRecords: a sorted list of FilesystemDataEvent_Record type objects for all variable types
        
        This function calls LabjackEventsLoader.loadLabjackEventsFile_loadFromFile(...) with a specific filepath
        
        
    """
    @staticmethod
    def loadBaseDataEventsFile(dataFilePath, videoDates, videoEndDates, shouldLimitEventsToVideoDates=True, limitedVariablesToCreateEventsFor=None, usePhoServerFormat=False, phoServerFormatIsStdOut=True, should_filter_for_invalid_events=True):
        ## Load the BaseData events data from an exported MATLAB file
        # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
        # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
        ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
        raise NotImplementedError
