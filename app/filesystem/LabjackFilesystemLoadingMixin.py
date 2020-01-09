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
# from app.filesystem.Workers.VideoMetadataWorkers import VideoMetadataWorker, VideoMetadataWorkerSignals
# from app.filesystem.Workers.VideoFilesystemWorkers import VideoFilesystemWorker, VideoFilesystemWorkerSignals
from app.filesystem.Workers.VideoMetadataWorkers import VideoMetadataWorker
from app.filesystem.Workers.VideoFilesystemWorkers import VideoFilesystemWorker

from pathlib import Path

from GUI.Model.ModelViewContainer import ModelViewContainer
from app.filesystem.FilesystemOperations import OperationTypes, PendingFilesystemOperation
from app.filesystem.LabjackEventsLoader import LabjackEventsLoader, PhoServerFormatArgs

from app.filesystem.FilesystemRecordBase import FilesystemRecordBase, FilesystemLabjackEvent_Record
from GUI.Model.Events.PhoDurationEvent import PhoDurationEvent

# from app.filesystem.LabjackFilesystemLoadingMixin import LabjackEventFile, LabjackFilesystemLoader


from pyqtgraph import ProgressDialog
import pyqtgraph as pg
class ProgressDialogDisplayingMixin(QObject):

    def __init__(self, filePath, parent=None):
        super().__init__(parent=parent)

        with ProgressDialog("Processing..", 0, 100, cancelText='Cancel', parent=self, busyCursor=True) as dlg:
            # do stuff
            self.get_labjack_data_files_loader().add_labjack_file_path(importFilePath)
            # dlg.setValue(i)   ## could also use dlg += 1
            dlg += 1
            if dlg.wasCanceled():
                raise Exception("Processing canceled by user")




""" LabjackEventFile: a single imported data file containing one or more labjack events.

"""
class LabjackEventFile(QObject):
    def __init__(self, filePath, parent=None):
        super().__init__(parent=parent)
        self.filePath = filePath
        self.dateTimes = []
        self.onesEventFormatDataArray = []
        self.variableData = []

        self.labjackContainerEvents = []
        # self.labjackEvents = []

        self.phoServerFormatArgs = None

    def get_file_path(self):
        return self.filePath

    def get_dateTimes(self):
        return self.dateTimes

    def get_variable_data(self):
        return self.variableData

    # def get_labjack_events(self):
    #     return self.labjackEvents

    def get_labjack_container_events(self):
        return self.labjackContainerEvents


    def get_parsed_dict(self):
        if self.phoServerFormatArgs is None:
            return None
        else:
            return self.phoServerFormatArgs.parsedFileInfoDict

    def set_loaded_values(self, dateTimes, onesEventFormatDataArray, variableData, labjackEventsContainerArray, phoServerFormatArgs):
        self.dateTimes = dateTimes
        self.onesEventFormatDataArray = onesEventFormatDataArray
        self.variableData = variableData
        # self.labjackEvents = labjackEvents
        self.labjackContainerEvents = labjackEventsContainerArray
        self.phoServerFormatArgs = phoServerFormatArgs


# QThreadPool

## LabjackFilesystemLoader: this object tries to find Labjack-exported data files in the filesystem and make them accessible in memory
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

        if (len(restricted_labjack_file_paths)>0):
            self.load_labjack_data_files(restricted_labjack_file_paths)

        self.targetLabjackDataFilePathsUpdated.emit()

    # # TODO: Integrate with the cache
    # def loadLabjackFile(self, aLabjackFilePath, videoStartDates, videoEndDates):
    #     print("LabjackFilesystemLoader.loadLabjackFile({0})".format(str(aLabjackFilePath)))
    #     outEventFileObj = LabjackEventFile(aLabjackFilePath)
    #     (dateTimes, onesEventFormatDataArray, variableData, labjackEvents) = LabjackFilesystemLoader.loadLabjackFiles(aLabjackFilePath, videoStartDates, videoEndDates, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
    #     outEventFileObj.set_loaded_values(dateTimes, onesEventFormatDataArray, variableData, labjackEvents)
    #     # Return the created object
    #     return outEventFileObj

    # The main function that starts the threads.
    def load_labjack_data_files(self, labjackDataFilePaths):
        print("LabjackFilesystemLoader.load_labjack_data_files(labjackDataFilePaths: {0})".format(str(labjackDataFilePaths)))
        # Pass the function to execute
        self.labjackFilesystemWorker = VideoMetadataWorker(labjackDataFilePaths, self.on_load_labjack_data_files_execute_thread) # Any other args, kwargs are passed to the run function
        self.labjackFilesystemWorker.signals.result.connect(self.on_load_labjack_data_files_print_output)
        self.labjackFilesystemWorker.signals.finished.connect(self.on_load_labjack_data_files_thread_complete)
        self.labjackFilesystemWorker.signals.progress.connect(self.on_load_labjack_data_files_progress_fn)
        
        # Execute
        self.threadpool.start(self.labjackFilesystemWorker) 


    ## Threads:
    @pyqtSlot(list, int)
    def on_load_labjack_data_files_progress_fn(self, active_labjack_data_file_paths, n):
        self.pending_operation_status.update(n)
        self.labjackDataFileLoaded.emit()
        print("%d%% done" % n)

    """
    The main execution function
    """
    def on_load_labjack_data_files_execute_thread(self, active_labjack_data_file_paths, progress_callback):
        currProgress = 0.0
        parsedFiles = 0
        numPendingFiles = len(active_labjack_data_file_paths)
        self.pending_operation_status.restart(OperationTypes.FilesystemLabjackFileLoad, numPendingFiles)

        # Loop through all the labjack data file paths and parse the files into a LabjackEventFile object.
        for (sub_index, aFoundLabjackDataFile) in enumerate(active_labjack_data_file_paths):

            # LabjackEventFile: this serves as a container to hold the loaded events
            outEventFileObj = LabjackEventFile(aFoundLabjackDataFile)

            # Call the static "loadLabjackEventsFile(...) function:

            # (dateTimes, onesEventFormatDataArray, variableData, labjackEvents) = LabjackFilesystemLoader.loadLabjackFiles(aFoundLabjackDataFile, self.videoStartDates, self.videoEndDates, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
            # (dateTimes, onesEventFormatDataArray, variableData, labjackEvents) = LabjackFilesystemLoader.loadLabjackEventsFile(aFoundLabjackDataFile, self.videoStartDates, self.videoEndDates, shouldLimitEventsToVideoDates=False, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
            (dateTimes, labjackEventContainers, phoServerFormatArgs) = LabjackFilesystemLoader.loadLabjackEventsFile(aFoundLabjackDataFile, self.videoStartDates, self.videoEndDates, shouldLimitEventsToVideoDates=False, usePhoServerFormat=True, phoServerFormatIsStdOut=False, should_filter_for_invalid_events=True)

            # Cache the loaded values into the LabjackEventFile object.
            outEventFileObj.set_loaded_values(dateTimes, [], [], labjackEventContainers, phoServerFormatArgs)
            
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






    @pyqtSlot(datetime, datetime)
    def set_start_end_video_file_dates(self, new_start_dates, new_end_dates):
        self.videoStartDates = np.array(new_start_dates)
        self.videoEndDates = np.array(new_end_dates)
        self.reload_on_labjack_paths_changed()


    @pyqtSlot(datetime, datetime, timedelta)
    def on_active_global_timeline_times_changed(self, totalStartTime, totalEndTime, totalDuration):
        # print("ReferenceMarkerManager.on_active_global_timeline_times_changed({0}, {1}, {2})".format(str(totalStartTime), str(totalEndTime), str(totalDuration)))
        # self.totalStartTime = totalStartTime
        # self.totalEndTime = totalEndTime
        # self.totalDuration = totalDuration
        return


    ## Static Methods:

    # @staticmethod
    # def loadLabjackFiles(labjackFilePath, videoDates, videoEndDates, shouldLimitEventsToVideoDates=True, limitedVariablesToCreateEventsFor=None, usePhoServerFormat=False, phoServerFormatIsStdOut=True):
    #     ## Load the Labjack events data from an exported MATLAB file
    #     # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
    #     # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
    #     ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
    #     if usePhoServerFormat:
    #         (relevantFileLines, relevantDateTimes, dateTimes, onesEventFormatDataArray) = LabjackEventsLoader.loadLabjackDataFromPhoServerFormat(labjackFilePath, shouldUseStdOutFormat=phoServerFormatIsStdOut)
    #     else:
    #         (dateNums, dateTimes, onesEventFormatDataArray) = LabjackEventsLoader.loadLabjackDataFromMatlabFormat(labjackFilePath)

    #     ## Pre-process the data
    #     if limitedVariablesToCreateEventsFor is not None:
    #         active_labjack_variable_names = limitedVariablesToCreateEventsFor

    #     else:
    #         active_labjack_variable_names = LabjackEventsLoader.labjack_variable_names

    #     numVariables = len(active_labjack_variable_names)

    #     earliestVideoTime = videoDates.min()
    #     latestVideoTime = videoEndDates.max()

    #     ## Iterate through the event variables and pre-process them
    #     variableData = []
    #     labjackEventRecords = []
    #     labjackEvents = []
    #     # Can't check for invalid events in here because we do it variable by variable.
    #     for variableIndex in range(0, numVariables):
    #         currVariableName = active_labjack_variable_names[variableIndex]
    #         dataArrayVariableIndex = LabjackEventsLoader.labjack_variable_indicies_dict[currVariableName]
    #         currVariableDataValues = onesEventFormatDataArray[:, dataArrayVariableIndex]
    #         currVariableColorTuple = mcolors.to_rgb(LabjackEventsLoader.labjack_variable_colors_dict[currVariableName])
    #         currVariableColor = QColor(int(255.0 * currVariableColorTuple[0]), int(255.0 * currVariableColorTuple[1]), int(255.0 * currVariableColorTuple[2]))

    #         # Find the non-zero entries for the current variable
    #         nonZeroEntries = np.nonzero(currVariableDataValues)
    #         activeValues = currVariableDataValues[nonZeroEntries] # This is just all ones for 0/1 array
    #         activeTimestamps = dateTimes[nonZeroEntries]

    #         labjackVariableSpecificRecords = []
    #         labjackVariableSpecificEvents = []
    #         ## Find times within video ranges:
    #         # activeVideoIndicies: contains an int index or None for each timestamp to indiciate which video (if any) the timestamp occured within
    #         activeVideoIndicies = np.empty_like(activeTimestamps)
    #         for index, anActiveTimestamp in enumerate(activeTimestamps):
    #             shouldCreateEvent = True
    #             video_relative_offset = None
    #             # Check if the timestamp is within the range of time that that videos span
    #             if (earliestVideoTime <= anActiveTimestamp <= latestVideoTime):
    #                 # Loop through each video to see if the event is included within its duration (not currently used)
    #                 for (videoIndex, videoStartDate) in enumerate(videoDates):
    #                     videoEndDate = videoEndDates[videoIndex]
    #                     if (videoStartDate <= anActiveTimestamp <= videoEndDate):
    #                         activeVideoIndicies[index] = videoIndex
    #                         video_relative_offset = anActiveTimestamp - videoStartDate
    #                         break
    #             else:
    #                 if shouldLimitEventsToVideoDates:
    #                     shouldCreateEvent = False

    #             if shouldCreateEvent:
    #                 currExtendedInfoDict = {'videoIndex': activeVideoIndicies[index],
    #                                         'video_relative_offset': video_relative_offset,
    #                                         'event_type':LabjackEventsLoader.labjack_variable_event_type[dataArrayVariableIndex],
    #                                         'dispense_type':LabjackEventsLoader.labjack_variable_event_type[dataArrayVariableIndex],
    #                                         'port': LabjackEventsLoader.labjack_variable_port_location[dataArrayVariableIndex],
    #                                         }
    #                 currRecord = FilesystemLabjackEvent_Record(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict)
    #                 labjackVariableSpecificRecords.append(currRecord)
    #                 currEvent = PhoDurationEvent(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict)
    #                 labjackVariableSpecificEvents.append(currEvent)

    #         # Append the variable-specific events to the master list of events
    #         labjackEventRecords.extend(labjackVariableSpecificRecords)
    #         labjackEvents.extend(labjackVariableSpecificEvents)
    #         variableData.append({'timestamps': activeTimestamps, 'values': activeValues, 'videoIndicies': activeVideoIndicies, 'variableSpecificEvents': labjackVariableSpecificEvents})

    #     labjackEventRecords = np.array(labjackEventRecords)
    #     labjackEvents = np.array(labjackEvents)
    #     # Sort events by timestamp
    #     try: import operator
    #     except ImportError: keyfun = lambda x: x.startTime  # use a lambda if no operator module
    #     else: keyfun = operator.attrgetter("startTime")  # use operator since it's faster than lambda
    #     labjackEvents = sorted(labjackEvents, key=keyfun)
    #     #sorted(labjackEvents, key=lambda i: i.startTime)

    #     ### Post-processing to detect erronious events, only for food2
    #     portNames = ['Water1', 'Water2', 'Food1', 'Food2']
    #     previousFoundDispenseEventTimestamp = {'Water1': None, 'Water2': None, 'Food1': None, 'Food2': None}
    #     previousFoundBeambreakEventTimestamp = {'Water1': None, 'Water2': None, 'Food1': None, 'Food2': None}
    #     invalidDispenseEventTimestamps = {'Water1': [], 'Water2': [], 'Food1': [], 'Food2': []}

    #     allInvalidDispenseEventTimestamps = []
    #     for index, anActiveEvent in enumerate(labjackEvents):

    #         if ((anActiveEvent.extended_data['event_type'] == 'BeamBreak')):
    #             currFoundBeambreakEventTimestamp = anActiveEvent.startTime
    #             previousFoundBeambreakEventTimestamp[anActiveEvent.extended_data['port']] = currFoundBeambreakEventTimestamp

    #         elif ((anActiveEvent.extended_data['event_type'] == 'Dispense')):
    #             currIsInvalidEvent = False
    #             currFoundDispenseEventTimestamp = anActiveEvent.startTime
    #             if (previousFoundBeambreakEventTimestamp[anActiveEvent.extended_data['port']] is None):
    #                 # If no beambreak preceeds it, it's invalid
    #                 currIsInvalidEvent = True

    #             else:
    #                 if (previousFoundDispenseEventTimestamp[anActiveEvent.extended_data['port']] is None):
    #                     #if no dispense event preceeds it there's no problem
    #                     pass
    #                 else:
    #                     if (previousFoundDispenseEventTimestamp[anActiveEvent.extended_data['port']] > previousFoundBeambreakEventTimestamp[anActiveEvent.extended_data['port']]):
    #                         # if the most recent dispense event is more recent then the last beambreak, there is a problem!
    #                         currIsInvalidEvent = True

    #             previousFoundDispenseEventTimestamp[anActiveEvent.extended_data['port']] = currFoundDispenseEventTimestamp

    #             if (currIsInvalidEvent):
    #                 invalidDispenseEventTimestamps[anActiveEvent.extended_data['port']].append(currFoundDispenseEventTimestamp)
    #                 allInvalidDispenseEventTimestamps.append(currFoundDispenseEventTimestamp)

    #         else:
    #             pass

    #     # # Filter the erroneous events from the individual arrays in each variableData
    #     # for index, aPort in enumerate(portNames):
    #     #     #print('Invalid dispense events detected: ', invalidDispenseEventIndicies)
    #     #     dispenseVariableIndex = index+4
    #     #     dispenseVariableTimestamps = np.array(variableData[dispenseVariableIndex]['timestamps'])
    #     #     dispenseVariableInvalidTimestamps = np.array(invalidDispenseEventTimestamps[aPort])
    #     #     print(aPort, ": ", len(dispenseVariableInvalidTimestamps), 'invalid dispense events out of', len(dispenseVariableTimestamps), 'events.')
    #     #     print("Removing invalid events...")
    #     #     dispenseVariableInvalidIndicies = np.isin(dispenseVariableTimestamps, dispenseVariableInvalidTimestamps)
    #     #     mask = np.ones(len(dispenseVariableTimestamps), dtype=bool)
    #     #     mask[dispenseVariableInvalidIndicies] = False
    #     #     variableData[dispenseVariableIndex]['timestamps'] = variableData[dispenseVariableIndex]['timestamps'][mask]
    #     #     variableData[dispenseVariableIndex]['values'] = variableData[dispenseVariableIndex]['values'][mask]
    #     #     variableData[dispenseVariableIndex]['variableSpecificEvents'] = np.array(variableData[dispenseVariableIndex]['variableSpecificEvents'])[mask]
    #     #     variableData[dispenseVariableIndex]['videoIndicies'] = variableData[dispenseVariableIndex]['videoIndicies'][mask]
    #     #
    #     #
    #     # # Filter the erroneous events from dateTimes and onesEventFormatDataArray
    #     # dispenseVariableAnyInvalidIndicies = np.isin(dateTimes, allInvalidDispenseEventTimestamps)
    #     # mask = np.ones(len(dateTimes), dtype=bool)
    #     # mask[dispenseVariableAnyInvalidIndicies] = False
    #     # dateTimes = dateTimes[mask]
    #     # onesEventFormatDataArray = onesEventFormatDataArray[mask]
    #     # if usePhoServerFormat:
    #     #     dispenseVariableAnyInvalidIndicies = np.isin(relevantDateTimes, allInvalidDispenseEventTimestamps)
    #     #     mask = np.ones(len(relevantDateTimes), dtype=bool)
    #     #     mask[dispenseVariableAnyInvalidIndicies] = False
    #     #     relevantFileLines = np.array(relevantFileLines)[mask]
    #     #     erroneousEventFreeCSVFilePath = r'C:\Users\halechr\repo\PhoPyQtTimelinePlotter\data\output\erroneousEventsRemoved.csv'
    #     #     print('Writing to CSV file:', erroneousEventFreeCSVFilePath)
    #     #     LabjackEventsLoader.writeLinesToCsvFile(relevantFileLines, filePath=erroneousEventFreeCSVFilePath)
    #     #     print('done.')

    #     return (dateTimes, onesEventFormatDataArray, variableData, labjackEvents)

    """ loadLabjackEventsFile_loadFromFile(...): Just loads the file
    Called by loadLabjackEventsFile(...)
        Calls the static LabjackEventsLoader functions for the appropriate file format (phoServer format or Matlab format).
        Returns a onesEventFormatDataArray.
    """
    @staticmethod
    def loadLabjackEventsFile_loadFromFile(labjackFilePath, usePhoServerFormat=False, phoServerFormatIsStdOut=True):
        ## Load the Labjack events data from an exported MATLAB file
        # Used only for PhoServerFormat:
        phoServerFormatArgs = None

        if usePhoServerFormat:
            parsedFileInfoDict = LabjackEventsLoader.parsePhoServerFormatFilepath(labjackFilePath)
            (phoServerFormatArgs, dateTimes, onesEventFormatDataArray) = LabjackEventsLoader.loadLabjackDataFromPhoServerFormat(labjackFilePath, shouldUseStdOutFormat=phoServerFormatIsStdOut)
            
        else:
            (dateNums, dateTimes, onesEventFormatDataArray) = LabjackEventsLoader.loadLabjackDataFromMatlabFormat(labjackFilePath)

        return (dateTimes, onesEventFormatDataArray, phoServerFormatArgs)

    """ loadLabjackEventsFile(...): new.

    """
    @staticmethod
    def loadLabjackEventsFile(labjackFilePath, videoDates, videoEndDates, shouldLimitEventsToVideoDates=True, limitedVariablesToCreateEventsFor=None, usePhoServerFormat=False, phoServerFormatIsStdOut=True, should_filter_for_invalid_events=True):
        ## Load the Labjack events data from an exported MATLAB file
        # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
        # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
        ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
        (dateTimes, onesEventFormatDataArray, phoServerFormatArgs) = LabjackFilesystemLoader.loadLabjackEventsFile_loadFromFile(labjackFilePath, usePhoServerFormat, phoServerFormatIsStdOut)

        ## Pre-process the data
        if limitedVariablesToCreateEventsFor is not None:
            active_labjack_variable_names = limitedVariablesToCreateEventsFor

        else:
            # Otherwise load for all variables
            active_labjack_variable_names = LabjackEventsLoader.labjack_variable_names

        numVariables = len(active_labjack_variable_names)

        earliestVideoTime = videoDates.min()
        latestVideoTime = videoEndDates.max()

        ## Iterate through the event variables and pre-process them
        variableData = []
        labjackEventRecords = []
        # labjackEvents = []
        # Can't check for invalid events in here because we do it variable by variable.
        for variableIndex in range(0, numVariables):
            currVariableName = active_labjack_variable_names[variableIndex]
            dataArrayVariableIndex = LabjackEventsLoader.labjack_variable_indicies_dict[currVariableName]
            currVariableDataValues = onesEventFormatDataArray[:, dataArrayVariableIndex]
            currVariableColorTuple = mcolors.to_rgb(LabjackEventsLoader.labjack_variable_colors_dict[currVariableName])
            currVariableColor = QColor(int(255.0 * currVariableColorTuple[0]), int(255.0 * currVariableColorTuple[1]), int(255.0 * currVariableColorTuple[2]))

            # Find the non-zero entries for the current variable
            nonZeroEntries = np.nonzero(currVariableDataValues)
            activeValues = currVariableDataValues[nonZeroEntries] # This is just all ones for 0/1 array
            activeTimestamps = dateTimes[nonZeroEntries]

            labjackVariableSpecificRecords = []
            # labjackVariableSpecificEvents = []
            ## Find times within video ranges:
            # activeVideoIndicies: contains an int index or None for each timestamp to indicate which video (if any) the timestamp occurred within
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
                                            'event_type':LabjackEventsLoader.labjack_variable_event_type[dataArrayVariableIndex],
                                            'dispense_type':LabjackEventsLoader.labjack_variable_event_type[dataArrayVariableIndex],
                                            'port': LabjackEventsLoader.labjack_variable_port_location[dataArrayVariableIndex],
                                            }
                    currRecord = FilesystemLabjackEvent_Record(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict, parent=None)
                    labjackVariableSpecificRecords.append(currRecord)
                    # currEvent = PhoDurationEvent(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict)
                    # currEvent = FilesystemLabjackEvent_Record.get_gui_view(currRecord, parent=None)
                    # labjackVariableSpecificEvents.append(currEvent)

            # Append the variable-specific events to the master list of events
            labjackEventRecords.extend(labjackVariableSpecificRecords)
            # labjackEvents.extend(labjackVariableSpecificEvents)
            # variableData.append({'timestamps': activeTimestamps, 'values': activeValues, 'videoIndicies': activeVideoIndicies, 'variableSpecificEvents': labjackVariableSpecificEvents})
            variableData.append({'timestamps': activeTimestamps, 'values': activeValues, 'videoIndicies': activeVideoIndicies, 'variableSpecificRecords': labjackVariableSpecificRecords})


        # Sort events by timestamp
        try: import operator
        except ImportError: keyfun = lambda x: x.start_date  # use a lambda if no operator module
        else: keyfun = operator.attrgetter("start_date")  # use operator since it's faster than lambda
        labjackEventRecords = sorted(labjackEventRecords, key=keyfun)

        # Be sure to convert into a numpy array AFTER sorting
        labjackEventRecords = np.array(labjackEventRecords)
        # labjackEvents = np.array(labjackEvents)

        if should_filter_for_invalid_events:
            print('Filtering for invalid events...')
            ### Post-processing to detect erronious events, only for food2
            dateTimes, onesEventFormatDataArray, variableData, labjackEventRecords, phoServerFormatArgs = LabjackFilesystemLoader.filter_invalid_events(dateTimes, onesEventFormatDataArray, variableData, labjackEventRecords, phoServerFormatArgs=phoServerFormatArgs)

        # Build the corresponding GUI objects
        ## TODO: defer until needed? Some might be filtered out anyway.
        built_model_view_container_array = []
        for (index, aRecord) in enumerate(labjackEventRecords):
            aGuiView = aRecord.get_gui_view(aRecord, parent=None)
            aModelViewContainer = ModelViewContainer(aRecord, aGuiView)
            built_model_view_container_array.append(aModelViewContainer)

        # labjackEvents = [FilesystemLabjackEvent_Record.get_gui_view(aRecord, parent=None) for aRecord in labjackEventRecords]


        # return (dateTimes, onesEventFormatDataArray, variableData, labjackEvents)
        return (dateTimes, built_model_view_container_array, phoServerFormatArgs)
