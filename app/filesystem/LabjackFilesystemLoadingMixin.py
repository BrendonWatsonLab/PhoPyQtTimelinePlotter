# LabjackFilesystemLoadingMixin.py
import sys
from datetime import datetime, timezone, timedelta
from enum import Enum
import numpy as np
import matplotlib.colors as mcolors

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingQObject

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult, CachedFileSource
# from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker, VideoMetadataWorkerSignals
# from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker, VideoFilesystemWorkerSignals
from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker
from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker

from pathlib import Path

from app.filesystem.FilesystemOperations import OperationTypes, PendingFilesystemOperation
from app.filesystem.LabjackEventsLoader import loadLabjackDataFromPhoServerFormat, loadLabjackDataFromMatlabFormat, labjack_variable_names, labjack_variable_colors_dict, labjack_variable_indicies_dict, labjack_variable_event_type, labjack_variable_port_location, writeLinesToCsvFile

from GUI.Model.Events.PhoDurationEvent import PhoDurationEvent

# from app.filesystem.LabjackFilesystemLoadingMixin import LabjackEventFile, LabjackFilesystemLoader

""" LabjackEventFile: a file

"""
class LabjackEventFile(QObject):
    def __init__(self, filePath, parent=None):
        super().__init__(parent=parent)
        self.filePath = filePath
        self.dateTimes = []
        self.onesEventFormatDataArray = []
        self.variableData = []
        self.labjackEvents = []

    def get_file_path(self):
        return self.filePath

    def get_dateTimes(self):
        return self.dateTimes

    def get_variable_data(self):
        return self.variableData

    def get_labjack_events(self):
        return self.labjackEvents

    def set_loaded_values(self, dateTimes, onesEventFormatDataArray, variableData, labjackEvents):
        self.dateTimes = dateTimes
        self.onesEventFormatDataArray = onesEventFormatDataArray
        self.variableData = variableData
        self.labjackEvents = labjackEvents




## LabjackFilesystemLoader: this object tries to find video files in the filesystem and add them to the database if they don't exist
"""
Loads the Labjack event files
"""
class LabjackFilesystemLoader(QObject):

    # foundFilesUpdated = pyqtSignal()
    targetLabjackDataFilePathsUpdated = pyqtSignal()

    labjackDataFileLoaded = pyqtSignal()
    loadingLabjackDataFilesComplete = pyqtSignal()


    def __init__(self, labjackFilePaths, parent=None):
        super(LabjackFilesystemLoader, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.cache = dict()
        self.labjackFilePaths = labjackFilePaths

        self.loadedLabjackFiles = []
        self.pending_operation_status = PendingFilesystemOperation(OperationTypes.NoOperation, 0, 0, parent=self)
        self.videoStartDates = []
        self.videoEndDates = []

        self.reload_on_labjack_paths_changed()
        
        self.labjackFilesystemWorker = None
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.reload_data()

    def get_cache(self):
        return self.cache

    @pyqtSlot(datetime, datetime)
    def set_start_end_video_file_dates(self, new_start_dates, new_end_dates):
        self.videoStartDates = np.array(new_start_dates)
        self.videoEndDates = np.array(new_end_dates)
        self.reload_on_labjack_paths_changed()


    # Called to add a new video path to generate thumbnails for
    def add_labjack_file_path(self, newLabjackFilePath):
        if (newLabjackFilePath in self.labjackFilePaths):
            print("WARNING: {0} is already in labjackFilePaths! Not adding again.".format(str(newLabjackFilePath)))
            return False
        
        # If it's in the array of already completed video files, skip it as well
        if (newLabjackFilePath in self.loadedLabjackFiles):
            print("WARNING: {0} is already in loadedLabjackFiles! It's already been processed, so we're not adding it again.".format(str(newLabjackFilePath)))
            return False

        # Otherwise we can add it
        self.labjackFilePaths.append(newLabjackFilePath)
        self.reload_on_labjack_paths_changed()


    def reload_on_labjack_paths_changed(self):
        print("LabjackFilesystemLoader.reload_on_labjack_paths_changed(...)")
        if (len(self.labjackFilePaths)>0):
            self.load_labjack_data_files(self.labjackFilePaths)
    
        self.targetLabjackDataFilePathsUpdated.emit()


    def reload_data(self, restricted_labjack_file_paths=None):
        print("VideoPreviewThumbnailGenerator.reload_data(...)")
        if restricted_labjack_file_paths is None:
            restricted_labjack_file_paths = self.labjackFilePaths

        self.load_labjack_data_files(restricted_labjack_file_paths)

        self.targetLabjackDataFilePathsUpdated.emit()


    # TODO: Integrate with the cache
    def loadLabjackFile(self, aLabjackFilePath, videoStartDates, videoEndDates):
        print("LabjackFilesystemLoader.loadLabjackFile({0})".format(str(aLabjackFilePath)))
        outEventFileObj = LabjackEventFile(aLabjackFilePath)
        (dateTimes, onesEventFormatDataArray, variableData, labjackEvents) = LabjackFilesystemLoader.loadLabjackFiles(aLabjackFilePath, videoStartDates, videoEndDates, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
        outEventFileObj.set_loaded_values(dateTimes, onesEventFormatDataArray, variableData, labjackEvents)
        # Return the created object
        return outEventFileObj

    @staticmethod
    def loadLabjackFiles(labjackFilePath, videoDates, videoEndDates, shouldLimitEventsToVideoDates=True, limitedVariablesToCreateEventsFor=None, usePhoServerFormat=False, phoServerFormatIsStdOut=True):
        ## Load the Labjack events data from an exported MATLAB file
        # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
        # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
        ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
        if usePhoServerFormat:
            (relevantFileLines, relevantDateTimes, dateTimes, onesEventFormatDataArray) = loadLabjackDataFromPhoServerFormat(labjackFilePath, shouldUseStdOutFormat=phoServerFormatIsStdOut)
        else:
            (dateNums, dateTimes, onesEventFormatDataArray) = loadLabjackDataFromMatlabFormat(labjackFilePath)

        ## Pre-process the data
        if limitedVariablesToCreateEventsFor:
            active_labjack_variable_names = limitedVariablesToCreateEventsFor

        else:
            active_labjack_variable_names = labjack_variable_names

        numVariables = len(active_labjack_variable_names)

        earliestVideoTime = videoDates.min()
        latestVideoTime = videoEndDates.max()

        ## Iterate through the event variables and pre-process them
        variableData = []
        labjackEvents = []
        # Can't check for invalid events in here because we do it variable by variable.
        for variableIndex in range(0, numVariables):
            currVariableName = active_labjack_variable_names[variableIndex]
            dataArrayVariableIndex = labjack_variable_indicies_dict[currVariableName]
            currVariableDataValues = onesEventFormatDataArray[:, dataArrayVariableIndex]
            currVariableColorTuple = mcolors.to_rgb(labjack_variable_colors_dict[currVariableName])
            currVariableColor = QColor(int(255.0 * currVariableColorTuple[0]), int(255.0 * currVariableColorTuple[1]), int(255.0 * currVariableColorTuple[2]))

            # Find the non-zero entries for the current variable
            nonZeroEntries = np.nonzero(currVariableDataValues)
            activeValues = currVariableDataValues[nonZeroEntries] # This is just all ones for 0/1 array
            activeTimestamps = dateTimes[nonZeroEntries]

            labjackVariableSpecificEvents = []
            ## Find times within video ranges:
            # activeVideoIndicies: contains an int index or None for each timestamp to indiciate which video (if any) the timestamp occured within
            activeVideoIndicies = np.empty_like(activeTimestamps)
            for index, anActiveTimestamp in enumerate(activeTimestamps):
                shouldCreateEvent = True
                video_relative_offset = None
                # Check if the timestamp is within the range of time that that videos span
                if (earliestVideoTime <= anActiveTimestamp <= latestVideoTime):
                    # Loop through each video to see if the event is included within its duration (not currently used)
                    for (videoIndex, videoStartDate) in enumerate(videoDates):
                        videoEndDate = videoEndDates[videoIndex]
                        if (videoStartDate <= anActiveTimestamp <= videoEndDate):
                            activeVideoIndicies[index] = videoIndex
                            video_relative_offset = anActiveTimestamp - videoStartDate
                            break
                else:
                    if shouldLimitEventsToVideoDates:
                        shouldCreateEvent = False

                if shouldCreateEvent:
                    currExtendedInfoDict = {'videoIndex': activeVideoIndicies[index],
                                            'video_relative_offset': video_relative_offset,
                                            'event_type':labjack_variable_event_type[dataArrayVariableIndex],
                                            'dispense_type':labjack_variable_event_type[dataArrayVariableIndex],
                                            'port': labjack_variable_port_location[dataArrayVariableIndex],
                                            }
                    currEvent = PhoDurationEvent(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict)
                    labjackVariableSpecificEvents.append(currEvent)

            # Append the variable-specific events to the master list of events
            labjackEvents.extend(labjackVariableSpecificEvents)
            variableData.append({'timestamps': activeTimestamps, 'values': activeValues, 'videoIndicies': activeVideoIndicies, 'variableSpecificEvents': labjackVariableSpecificEvents})

        labjackEvents = np.array(labjackEvents)
        # Sort events by timestamp
        try: import operator
        except ImportError: keyfun = lambda x: x.startTime  # use a lambda if no operator module
        else: keyfun = operator.attrgetter("startTime")  # use operator since it's faster than lambda
        labjackEvents = sorted(labjackEvents, key=keyfun)
        #sorted(labjackEvents, key=lambda i: i.startTime)

        ### Post-processing to detect erronious events, only for food2
        portNames = ['Water1', 'Water2', 'Food1', 'Food2']
        previousFoundDispenseEventTimestamp = {'Water1': None, 'Water2': None, 'Food1': None, 'Food2': None}
        previousFoundBeambreakEventTimestamp = {'Water1': None, 'Water2': None, 'Food1': None, 'Food2': None}
        invalidDispenseEventTimestamps = {'Water1': [], 'Water2': [], 'Food1': [], 'Food2': []}

        allInvalidDispenseEventTimestamps = []
        for index, anActiveEvent in enumerate(labjackEvents):

            if ((anActiveEvent.extended_data['event_type'] == 'BeamBreak')):
                currFoundBeambreakEventTimestamp = anActiveEvent.startTime
                previousFoundBeambreakEventTimestamp[anActiveEvent.extended_data['port']] = currFoundBeambreakEventTimestamp

            elif ((anActiveEvent.extended_data['event_type'] == 'Dispense')):
                currIsInvalidEvent = False
                currFoundDispenseEventTimestamp = anActiveEvent.startTime
                if (previousFoundBeambreakEventTimestamp[anActiveEvent.extended_data['port']] is None):
                    # If no beambreak preceeds it, it's invalid
                    currIsInvalidEvent = True

                else:
                    if (previousFoundDispenseEventTimestamp[anActiveEvent.extended_data['port']] is None):
                        #if no dispense event preceeds it there's no problem
                        pass
                    else:
                        if (previousFoundDispenseEventTimestamp[anActiveEvent.extended_data['port']] > previousFoundBeambreakEventTimestamp[anActiveEvent.extended_data['port']]):
                            # if the most recent dispense event is more recent then the last beambreak, there is a problem!
                            currIsInvalidEvent = True

                previousFoundDispenseEventTimestamp[anActiveEvent.extended_data['port']] = currFoundDispenseEventTimestamp

                if (currIsInvalidEvent):
                    invalidDispenseEventTimestamps[anActiveEvent.extended_data['port']].append(currFoundDispenseEventTimestamp)
                    allInvalidDispenseEventTimestamps.append(currFoundDispenseEventTimestamp)

            else:
                pass

        # Filter the erroneous events from the individual arrays in each variableData
        for index, aPort in enumerate(portNames):
            #print('Invalid dispense events detected: ', invalidDispenseEventIndicies)
            dispenseVariableIndex = index+4
            dispenseVariableTimestamps = np.array(variableData[dispenseVariableIndex]['timestamps'])
            dispenseVariableInvalidTimestamps = np.array(invalidDispenseEventTimestamps[aPort])
            print(aPort, ": ", len(dispenseVariableInvalidTimestamps), 'invalid dispense events out of', len(dispenseVariableTimestamps), 'events.')
            print("Removing invalid events...")
            dispenseVariableInvalidIndicies = np.isin(dispenseVariableTimestamps, dispenseVariableInvalidTimestamps)
            mask = np.ones(len(dispenseVariableTimestamps), dtype=bool)
            mask[dispenseVariableInvalidIndicies] = False
            variableData[dispenseVariableIndex]['timestamps'] = variableData[dispenseVariableIndex]['timestamps'][mask]
            variableData[dispenseVariableIndex]['values'] = variableData[dispenseVariableIndex]['values'][mask]
            variableData[dispenseVariableIndex]['variableSpecificEvents'] = np.array(variableData[dispenseVariableIndex]['variableSpecificEvents'])[mask]
            variableData[dispenseVariableIndex]['videoIndicies'] = variableData[dispenseVariableIndex]['videoIndicies'][mask]


        # Filter the erroneous events from dateTimes and onesEventFormatDataArray
        dispenseVariableAnyInvalidIndicies = np.isin(dateTimes, allInvalidDispenseEventTimestamps)
        mask = np.ones(len(dateTimes), dtype=bool)
        mask[dispenseVariableAnyInvalidIndicies] = False
        dateTimes = dateTimes[mask]
        onesEventFormatDataArray = onesEventFormatDataArray[mask]
        if usePhoServerFormat:
            dispenseVariableAnyInvalidIndicies = np.isin(relevantDateTimes, allInvalidDispenseEventTimestamps)
            mask = np.ones(len(relevantDateTimes), dtype=bool)
            mask[dispenseVariableAnyInvalidIndicies] = False
            relevantFileLines = np.array(relevantFileLines)[mask]
            erroneousEventFreeCSVFilePath = r'C:\Users\halechr\repo\PhoPyQtTimelinePlotter\data\output\erroneousEventsRemoved.csv'
            print('Writing to CSV file:', erroneousEventFreeCSVFilePath)
            writeLinesToCsvFile(relevantFileLines, filePath=erroneousEventFreeCSVFilePath)
            print('done.')

        return (dateTimes, onesEventFormatDataArray, variableData, labjackEvents)
        

        ## generate_video_thumbnails:
        # Finds the video metadata in a multithreaded way
    
    
    
    def load_labjack_data_files(self, labjackDataFilePaths):
        print("LabjackFilesystemLoader.load_labjack_data_files(labjackDataFilePaths: {0})".format(str(labjackDataFilePaths)))
        # Pass the function to execute
        self.labjackFilesystemWorker = VideoMetadataWorker(labjackDataFilePaths, self.on_load_labjack_data_files_execute_thread) # Any other args, kwargs are passed to the run function
        self.labjackFilesystemWorker.signals.result.connect(self.on_load_labjack_data_files_print_output)
        self.labjackFilesystemWorker.signals.finished.connect(self.on_load_labjack_data_files_thread_complete)
        self.labjackFilesystemWorker.signals.progress.connect(self.on_load_labjack_data_files_progress_fn)
        
        # Execute
        self.threadpool.start(self.labjackFilesystemWorker) 


    # Threads:
    @pyqtSlot(list, int)
    def on_load_labjack_data_files_progress_fn(self, active_labjack_data_file_paths, n):
        self.pending_operation_status.update(n)
        self.labjackDataFileLoaded.emit()
        print("%d%% done" % n)

    def on_load_labjack_data_files_execute_thread(self, active_labjack_data_file_paths, progress_callback):
        currProgress = 0.0
        parsedFiles = 0
        numPendingFiles = len(active_labjack_data_file_paths)
        self.pending_operation_status.restart(OperationTypes.FilesystemLabjackFileLoad, numPendingFiles)

        for (sub_index, aFoundLabjackDataFile) in enumerate(active_labjack_data_file_paths):

            outEventFileObj = LabjackEventFile(aFoundLabjackDataFile)
            (dateTimes, onesEventFormatDataArray, variableData, labjackEvents) = LabjackFilesystemLoader.loadLabjackFiles(aFoundLabjackDataFile, self.videoStartDates, self.videoEndDates, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
            outEventFileObj.set_loaded_values(dateTimes, onesEventFormatDataArray, variableData, labjackEvents)
            
            if (not (aFoundLabjackDataFile in self.cache.keys())):
                # Parent doesn't yet exist in cache
                self.cache[aFoundLabjackDataFile] = outEventFileObj
            else:
                # Parent already exists
                print("WARNING: video path {0} already exists in the cache. Updating its thumbnail objects list...".format(str(aFoundLabjackDataFile)))
                self.cache[aFoundLabjackDataFile] = outEventFileObj
                pass

            # Add the current video file path to the loaded files
            self.loadedLabjackFiles.append(aFoundLabjackDataFile)

            parsedFiles = parsedFiles + 1
            progress_callback.emit(active_labjack_data_file_paths, (parsedFiles*100/numPendingFiles))

        return "Done."
 
    @pyqtSlot(list, object)
    def on_load_labjack_data_files_print_output(self, active_video_paths, s):
        print(s)
        
    @pyqtSlot(list)
    def on_load_labjack_data_files_thread_complete(self, finished_loaded_labjack_data_files):
        print("THREAD on_load_labjack_data_files_thread_complete(...)! {0}".format(str(finished_loaded_labjack_data_files)))
        # The finished_loaded_labjack_data_files are paths that have already been added to self.loadedLabjackFiles. We just need to remove them from self.labjackFilePaths
        for aFinishedVideoFilePath in finished_loaded_labjack_data_files:
            self.labjackFilePaths.remove(aFinishedVideoFilePath)

        self.loadingLabjackDataFilesComplete.emit()



