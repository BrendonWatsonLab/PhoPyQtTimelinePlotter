# DeeplabcutOutputFilesystemLoadingMixin.py
import sys
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

from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker

from pathlib import Path

from GUI.Model.ModelViewContainer import ModelViewContainer
from app.filesystem.FilesystemOperations import OperationTypes, PendingFilesystemOperation
from app.filesystem.FilesystemRecordBase import FilesystemRecordBase
from GUI.Model.Events.PhoDurationEvent import PhoDurationEvent

# from app.filesystem.DeeplabcutOutputFilesystemLoadingMixin import DeeplabCutOutputFileType, DeeplabcutEventFile, DeeplabcutFilesystemLoader


class DeeplabCutOutputFileType(Enum):
    CSV = 1
    HDF = 2
    EXCEL = 3
    PICKLE = 3

    @staticmethod
    def get_from_extension(file_extension):
        if (file_extension == ".csv"):
            return DeeplabCutOutputFileType.CSV
        elif (file_extension == ".h5"):
            return DeeplabCutOutputFileType.HDF
        elif (file_extension == ".xls"):
            return DeeplabCutOutputFileType.EXCEL
        elif (file_extension == ".pickle"):
            return DeeplabCutOutputFileType.PICKLE
        else:
            print("UNIMPLEMENTED!!")
            return None

""" DeeplabcutEventFile: a file

"""
class DeeplabcutEventFile(QObject):

    dataReloaded = pyqtSignal(pd.DataFrame)


    def __init__(self, filePath, file_format, parent=None):
        super().__init__(parent=parent)
        self.filePath = filePath
        self.file_format = file_format
        self.data = None
        # self.dateTimes = []
        # self.onesEventFormatDataArray = []
        # self.variableData = []
        # self.deeplabcutContainerEvents = []

    def get_file_path(self):
        return self.filePath

    def get_file_format(self):
        return self.file_format

    def get_loaded_data(self):
        return self.data

    # def get_dateTimes(self):
    #     return self.dateTimes

    # def get_variable_data(self):
    #     return self.variableData

    # def get_deeplabcut_container_events(self):
    #     return self.deeplabcutContainerEvents

    # Loads the data file provided
    def load_data(self):
        if (self.file_format == DeeplabCutOutputFileType.CSV):
            self.data = pd.read_csv(self.get_file_path())

        elif (self.file_format == DeeplabCutOutputFileType.HDF):
            self.data = pd.read_hdf(self.get_file_path())

        elif (self.file_format == DeeplabCutOutputFileType.EXCEL):
            self.data = pd.read_excel(self.get_file_path(), 'Sheet1', index_col=None, na_values=['NA'])

        else:
            print("Unimplemented error!")
            self.data = None
            return
        
        self.dataReloaded.emit(self.data)

        
    # def set_loaded_values(self, dateTimes, onesEventFormatDataArray, variableData, deeplabcutEvents):
    #     self.dateTimes = dateTimes
    #     self.onesEventFormatDataArray = onesEventFormatDataArray
    #     self.variableData = variableData
    #     self.deeplabcutEvents = deeplabcutEvents

    # def set_loaded_values(self, dateTimes, onesEventFormatDataArray, variableData, deeplabcutEventsContainerArray):
    #     self.dateTimes = dateTimes
    #     self.onesEventFormatDataArray = onesEventFormatDataArray
    #     self.variableData = variableData
    #     # self.deeplabcutEvents = deeplabcutEvents
    #     self.deeplabcutContainerEvents = deeplabcutEventsContainerArray




## DeeplabcutFilesystemLoader: this object tries to find video files in the filesystem and add them to the database if they don't exist
"""
Loads the Deeplabcut event files
"""
class DeeplabcutFilesystemLoader(QObject):

    # foundFilesUpdated = pyqtSignal()
    targetDeeplabcutDataFilePathsUpdated = pyqtSignal()

    deeplabcutDataFileLoaded = pyqtSignal()
    loadingDeeplabcutDataFilesComplete = pyqtSignal()


    def __init__(self, deeplabcutFilePaths, parent=None):
        super(DeeplabcutFilesystemLoader, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.cache = dict()
        self.deeplabcutFilePaths = deeplabcutFilePaths

        self.loadedDeeplabcutFiles = []
        self.pending_operation_status = PendingFilesystemOperation(OperationTypes.NoOperation, 0, 0, parent=self)
        self.videoStartDates = []
        self.videoEndDates = []

        self.reload_on_deeplabcut_paths_changed()
        
        self.deeplabcutFilesystemWorker = None
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.reload_data()

    def get_cache(self):
        return self.cache

    # Called to add a new video path to generate thumbnails for
    def add_deeplabcut_file_path(self, newDeeplabcutFilePath):
        if (newDeeplabcutFilePath in self.deeplabcutFilePaths):
            print("WARNING: {0} is already in deeplabcutFilePaths! Not adding again.".format(str(newDeeplabcutFilePath)))
            return False
        
        # If it's in the array of already completed video files, skip it as well
        if (newDeeplabcutFilePath in self.loadedDeeplabcutFiles):
            print("WARNING: {0} is already in loadedDeeplabcutFiles! It's already been processed, so we're not adding it again.".format(str(newDeeplabcutFilePath)))
            return False

        # Otherwise we can add it
        self.deeplabcutFilePaths.append(newDeeplabcutFilePath)
        self.reload_on_deeplabcut_paths_changed()

    def reload_on_deeplabcut_paths_changed(self):
        print("DeeplabcutFilesystemLoader.reload_on_deeplabcut_paths_changed(...)")
        if (len(self.deeplabcutFilePaths)>0):
            self.load_deeplabcut_data_files(self.deeplabcutFilePaths)
    
        self.targetDeeplabcutDataFilePathsUpdated.emit()


    def reload_data(self, restricted_deeplabcut_file_paths=None):
        print("VideoPreviewThumbnailGenerator.reload_data(...)")
        if restricted_deeplabcut_file_paths is None:
            restricted_deeplabcut_file_paths = self.deeplabcutFilePaths

        if (len(restricted_deeplabcut_file_paths)>0):
            self.load_deeplabcut_data_files(restricted_deeplabcut_file_paths)

        self.targetDeeplabcutDataFilePathsUpdated.emit()


    # # TODO: Integrate with the cache
    # def loadDeeplabcutFile(self, aDeeplabcutFilePath, videoStartDates, videoEndDates):
    #     print("DeeplabcutFilesystemLoader.loadDeeplabcutFile({0})".format(str(aDeeplabcutFilePath)))
    #     outEventFileObj = DeeplabcutEventFile(aDeeplabcutFilePath)
    #     (dateTimes, onesEventFormatDataArray, variableData, deeplabcutEvents) = DeeplabcutFilesystemLoader.loadDeeplabcutFiles(aDeeplabcutFilePath, videoStartDates, videoEndDates, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
    #     outEventFileObj.set_loaded_values(dateTimes, onesEventFormatDataArray, variableData, deeplabcutEvents)
    #     # Return the created object
    #     return outEventFileObj

    @staticmethod
    def loadDeeplabcutFiles(deeplabcutFilePath, videoDates, videoEndDates, shouldLimitEventsToVideoDates=True, limitedVariablesToCreateEventsFor=None, usePhoServerFormat=False, phoServerFormatIsStdOut=True):
        ## Load the Deeplabcut events data from an exported MATLAB file
        # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
        # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
        ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
        if usePhoServerFormat:
            (relevantFileLines, relevantDateTimes, dateTimes, onesEventFormatDataArray) = DeeplabcutEventsLoader.loadDeeplabcutDataFromPhoServerFormat(deeplabcutFilePath, shouldUseStdOutFormat=phoServerFormatIsStdOut)
        else:
            (dateNums, dateTimes, onesEventFormatDataArray) = DeeplabcutEventsLoader.loadDeeplabcutDataFromMatlabFormat(deeplabcutFilePath)

        ## Pre-process the data
        if limitedVariablesToCreateEventsFor is not None:
            active_deeplabcut_variable_names = limitedVariablesToCreateEventsFor

        else:
            active_deeplabcut_variable_names = DeeplabcutEventsLoader.deeplabcut_variable_names

        numVariables = len(active_deeplabcut_variable_names)

        earliestVideoTime = videoDates.min()
        latestVideoTime = videoEndDates.max()

        ## Iterate through the event variables and pre-process them
        variableData = []
        deeplabcutEventRecords = []
        deeplabcutEvents = []
        # Can't check for invalid events in here because we do it variable by variable.
        for variableIndex in range(0, numVariables):
            currVariableName = active_deeplabcut_variable_names[variableIndex]
            dataArrayVariableIndex = DeeplabcutEventsLoader.deeplabcut_variable_indicies_dict[currVariableName]
            currVariableDataValues = onesEventFormatDataArray[:, dataArrayVariableIndex]
            currVariableColorTuple = mcolors.to_rgb(DeeplabcutEventsLoader.deeplabcut_variable_colors_dict[currVariableName])
            currVariableColor = QColor(int(255.0 * currVariableColorTuple[0]), int(255.0 * currVariableColorTuple[1]), int(255.0 * currVariableColorTuple[2]))

            # Find the non-zero entries for the current variable
            nonZeroEntries = np.nonzero(currVariableDataValues)
            activeValues = currVariableDataValues[nonZeroEntries] # This is just all ones for 0/1 array
            activeTimestamps = dateTimes[nonZeroEntries]

            deeplabcutVariableSpecificRecords = []
            deeplabcutVariableSpecificEvents = []
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
                                            'event_type':DeeplabcutEventsLoader.deeplabcut_variable_event_type[dataArrayVariableIndex],
                                            'dispense_type':DeeplabcutEventsLoader.deeplabcut_variable_event_type[dataArrayVariableIndex],
                                            'port': DeeplabcutEventsLoader.deeplabcut_variable_port_location[dataArrayVariableIndex],
                                            }
                    currRecord = FilesystemDeeplabcutEvent_Record(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict)
                    deeplabcutVariableSpecificRecords.append(currRecord)
                    currEvent = PhoDurationEvent(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict)
                    deeplabcutVariableSpecificEvents.append(currEvent)

            # Append the variable-specific events to the master list of events
            deeplabcutEventRecords.extend(deeplabcutVariableSpecificRecords)
            deeplabcutEvents.extend(deeplabcutVariableSpecificEvents)
            variableData.append({'timestamps': activeTimestamps, 'values': activeValues, 'videoIndicies': activeVideoIndicies, 'variableSpecificEvents': deeplabcutVariableSpecificEvents})

        deeplabcutEventRecords = np.array(deeplabcutEventRecords)
        deeplabcutEvents = np.array(deeplabcutEvents)
        # Sort events by timestamp
        try: import operator
        except ImportError: keyfun = lambda x: x.startTime  # use a lambda if no operator module
        else: keyfun = operator.attrgetter("startTime")  # use operator since it's faster than lambda
        deeplabcutEvents = sorted(deeplabcutEvents, key=keyfun)
        #sorted(deeplabcutEvents, key=lambda i: i.startTime)

        ### Post-processing to detect erronious events, only for food2
        portNames = ['Water1', 'Water2', 'Food1', 'Food2']
        previousFoundDispenseEventTimestamp = {'Water1': None, 'Water2': None, 'Food1': None, 'Food2': None}
        previousFoundBeambreakEventTimestamp = {'Water1': None, 'Water2': None, 'Food1': None, 'Food2': None}
        invalidDispenseEventTimestamps = {'Water1': [], 'Water2': [], 'Food1': [], 'Food2': []}

        allInvalidDispenseEventTimestamps = []
        for index, anActiveEvent in enumerate(deeplabcutEvents):

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

        # # Filter the erroneous events from the individual arrays in each variableData
        # for index, aPort in enumerate(portNames):
        #     #print('Invalid dispense events detected: ', invalidDispenseEventIndicies)
        #     dispenseVariableIndex = index+4
        #     dispenseVariableTimestamps = np.array(variableData[dispenseVariableIndex]['timestamps'])
        #     dispenseVariableInvalidTimestamps = np.array(invalidDispenseEventTimestamps[aPort])
        #     print(aPort, ": ", len(dispenseVariableInvalidTimestamps), 'invalid dispense events out of', len(dispenseVariableTimestamps), 'events.')
        #     print("Removing invalid events...")
        #     dispenseVariableInvalidIndicies = np.isin(dispenseVariableTimestamps, dispenseVariableInvalidTimestamps)
        #     mask = np.ones(len(dispenseVariableTimestamps), dtype=bool)
        #     mask[dispenseVariableInvalidIndicies] = False
        #     variableData[dispenseVariableIndex]['timestamps'] = variableData[dispenseVariableIndex]['timestamps'][mask]
        #     variableData[dispenseVariableIndex]['values'] = variableData[dispenseVariableIndex]['values'][mask]
        #     variableData[dispenseVariableIndex]['variableSpecificEvents'] = np.array(variableData[dispenseVariableIndex]['variableSpecificEvents'])[mask]
        #     variableData[dispenseVariableIndex]['videoIndicies'] = variableData[dispenseVariableIndex]['videoIndicies'][mask]
        #
        #
        # # Filter the erroneous events from dateTimes and onesEventFormatDataArray
        # dispenseVariableAnyInvalidIndicies = np.isin(dateTimes, allInvalidDispenseEventTimestamps)
        # mask = np.ones(len(dateTimes), dtype=bool)
        # mask[dispenseVariableAnyInvalidIndicies] = False
        # dateTimes = dateTimes[mask]
        # onesEventFormatDataArray = onesEventFormatDataArray[mask]
        # if usePhoServerFormat:
        #     dispenseVariableAnyInvalidIndicies = np.isin(relevantDateTimes, allInvalidDispenseEventTimestamps)
        #     mask = np.ones(len(relevantDateTimes), dtype=bool)
        #     mask[dispenseVariableAnyInvalidIndicies] = False
        #     relevantFileLines = np.array(relevantFileLines)[mask]
        #     erroneousEventFreeCSVFilePath = r'C:\Users\halechr\repo\PhoPyQtTimelinePlotter\data\output\erroneousEventsRemoved.csv'
        #     print('Writing to CSV file:', erroneousEventFreeCSVFilePath)
        #     DeeplabcutEventsLoader.writeLinesToCsvFile(relevantFileLines, filePath=erroneousEventFreeCSVFilePath)
        #     print('done.')

        return (dateTimes, onesEventFormatDataArray, variableData, deeplabcutEvents)

    """ loadDeeplabcutEventsFile_loadFromFile(...): Just loads the file

    """
    @staticmethod
    def loadDeeplabcutEventsFile_loadFromFile(deeplabcutFilePath, usePhoServerFormat=False, phoServerFormatIsStdOut=True):
        ## Load the Deeplabcut events data from an exported MATLAB file
        # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
        # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
        ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
        if usePhoServerFormat:
            (relevantFileLines, relevantDateTimes, dateTimes, onesEventFormatDataArray) = DeeplabcutEventsLoader.loadDeeplabcutDataFromPhoServerFormat(deeplabcutFilePath, shouldUseStdOutFormat=phoServerFormatIsStdOut)
        else:
            (dateNums, dateTimes, onesEventFormatDataArray) = DeeplabcutEventsLoader.loadDeeplabcutDataFromMatlabFormat(deeplabcutFilePath)

        return (dateTimes, onesEventFormatDataArray)

    """ loadDeeplabcutEventsFile(...): new.

    """
    @staticmethod
    def loadDeeplabcutEventsFile(deeplabcutFilePath, videoDates, videoEndDates, shouldLimitEventsToVideoDates=True, limitedVariablesToCreateEventsFor=None, usePhoServerFormat=False, phoServerFormatIsStdOut=True):
        ## Load the Deeplabcut events data from an exported MATLAB file
        # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
        # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
        ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
        (dateTimes, onesEventFormatDataArray) = DeeplabcutFilesystemLoader.loadDeeplabcutEventsFile_loadFromFile(deeplabcutFilePath, usePhoServerFormat, phoServerFormatIsStdOut)

        ## Pre-process the data
        if limitedVariablesToCreateEventsFor is not None:
            active_deeplabcut_variable_names = limitedVariablesToCreateEventsFor

        else:
            active_deeplabcut_variable_names = DeeplabcutEventsLoader.deeplabcut_variable_names

        numVariables = len(active_deeplabcut_variable_names)

        earliestVideoTime = videoDates.min()
        latestVideoTime = videoEndDates.max()

        ## Iterate through the event variables and pre-process them
        variableData = []
        deeplabcutEventRecords = []
        deeplabcutEvents = []
        # Can't check for invalid events in here because we do it variable by variable.
        for variableIndex in range(0, numVariables):
            currVariableName = active_deeplabcut_variable_names[variableIndex]
            dataArrayVariableIndex = DeeplabcutEventsLoader.deeplabcut_variable_indicies_dict[currVariableName]
            currVariableDataValues = onesEventFormatDataArray[:, dataArrayVariableIndex]
            currVariableColorTuple = mcolors.to_rgb(DeeplabcutEventsLoader.deeplabcut_variable_colors_dict[currVariableName])
            currVariableColor = QColor(int(255.0 * currVariableColorTuple[0]), int(255.0 * currVariableColorTuple[1]), int(255.0 * currVariableColorTuple[2]))

            # Find the non-zero entries for the current variable
            nonZeroEntries = np.nonzero(currVariableDataValues)
            activeValues = currVariableDataValues[nonZeroEntries] # This is just all ones for 0/1 array
            activeTimestamps = dateTimes[nonZeroEntries]

            deeplabcutVariableSpecificRecords = []
            # deeplabcutVariableSpecificEvents = []
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
                                            'event_type':DeeplabcutEventsLoader.deeplabcut_variable_event_type[dataArrayVariableIndex],
                                            'dispense_type':DeeplabcutEventsLoader.deeplabcut_variable_event_type[dataArrayVariableIndex],
                                            'port': DeeplabcutEventsLoader.deeplabcut_variable_port_location[dataArrayVariableIndex],
                                            }
                    currRecord = FilesystemDeeplabcutEvent_Record(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict, parent=None)
                    deeplabcutVariableSpecificRecords.append(currRecord)
                    # currEvent = PhoDurationEvent(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict)
                    # currEvent = FilesystemDeeplabcutEvent_Record.get_gui_view(currRecord, parent=None)
                    # deeplabcutVariableSpecificEvents.append(currEvent)

            # Append the variable-specific events to the master list of events
            deeplabcutEventRecords.extend(deeplabcutVariableSpecificRecords)
            # deeplabcutEvents.extend(deeplabcutVariableSpecificEvents)
            # variableData.append({'timestamps': activeTimestamps, 'values': activeValues, 'videoIndicies': activeVideoIndicies, 'variableSpecificEvents': deeplabcutVariableSpecificEvents})
            variableData.append({'timestamps': activeTimestamps, 'values': activeValues, 'videoIndicies': activeVideoIndicies, 'variableSpecificRecords': deeplabcutVariableSpecificRecords})


        deeplabcutEventRecords = np.array(deeplabcutEventRecords)
        # deeplabcutEvents = np.array(deeplabcutEvents)

        # Sort events by timestamp
        try: import operator
        except ImportError: keyfun = lambda x: x.start_date  # use a lambda if no operator module
        else: keyfun = operator.attrgetter("start_date")  # use operator since it's faster than lambda
        deeplabcutEventRecords = sorted(deeplabcutEventRecords, key=keyfun)


        # Build the corresponding GUI objects
        built_model_view_container_array = []
        for (index, aRecord) in enumerate(deeplabcutEventRecords):
            aGuiView = aRecord.get_gui_view(aRecord, parent=None)
            aModelViewContainer = ModelViewContainer(aRecord, aGuiView)
            built_model_view_container_array.append(aModelViewContainer)


        # return (dateTimes, onesEventFormatDataArray, variableData, deeplabcutEvents)
        return (dateTimes, built_model_view_container_array)

    def load_deeplabcut_data_files(self, deeplabcutDataFilePaths):
        print("DeeplabcutFilesystemLoader.load_deeplabcut_data_files(deeplabcutDataFilePaths: {0})".format(str(deeplabcutDataFilePaths)))
        # Pass the function to execute
        self.deeplabcutFilesystemWorker = VideoMetadataWorker(deeplabcutDataFilePaths, self.on_load_deeplabcut_data_files_execute_thread) # Any other args, kwargs are passed to the run function
        self.deeplabcutFilesystemWorker.signals.result.connect(self.on_load_deeplabcut_data_files_print_output)
        self.deeplabcutFilesystemWorker.signals.finished.connect(self.on_load_deeplabcut_data_files_thread_complete)
        self.deeplabcutFilesystemWorker.signals.progress.connect(self.on_load_deeplabcut_data_files_progress_fn)
        
        # Execute
        self.threadpool.start(self.deeplabcutFilesystemWorker) 


    # Threads:
    @pyqtSlot(list, int)
    def on_load_deeplabcut_data_files_progress_fn(self, active_deeplabcut_data_file_paths, n):
        self.pending_operation_status.update(n)
        self.deeplabcutDataFileLoaded.emit()
        print("%d%% done" % n)

    def on_load_deeplabcut_data_files_execute_thread(self, active_deeplabcut_data_file_paths, progress_callback):
        currProgress = 0.0
        parsedFiles = 0
        numPendingFiles = len(active_deeplabcut_data_file_paths)
        self.pending_operation_status.restart(OperationTypes.FilesystemDeeplabcutFileLoad, numPendingFiles)

        for (sub_index, aFoundDeeplabcutDataFile) in enumerate(active_deeplabcut_data_file_paths):

            outEventFileObj = DeeplabcutEventFile(aFoundDeeplabcutDataFile)
            # (dateTimes, onesEventFormatDataArray, variableData, deeplabcutEvents) = DeeplabcutFilesystemLoader.loadDeeplabcutFiles(aFoundDeeplabcutDataFile, self.videoStartDates, self.videoEndDates, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
            # (dateTimes, onesEventFormatDataArray, variableData, deeplabcutEvents) = DeeplabcutFilesystemLoader.loadDeeplabcutEventsFile(aFoundDeeplabcutDataFile, self.videoStartDates, self.videoEndDates, shouldLimitEventsToVideoDates=False, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
            
            (dateTimes, deeplabcutEventContainers) = DeeplabcutFilesystemLoader.loadDeeplabcutEventsFile(aFoundDeeplabcutDataFile, self.videoStartDates, self.videoEndDates, shouldLimitEventsToVideoDates=False, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
            outEventFileObj.set_loaded_values(dateTimes, [], [], deeplabcutEventContainers)
            
            if (not (aFoundDeeplabcutDataFile in self.cache.keys())):
                # Parent doesn't yet exist in cache
                self.cache[aFoundDeeplabcutDataFile] = outEventFileObj
            else:
                # Parent already exists
                print("WARNING: video path {0} already exists in the cache. Updating its thumbnail objects list...".format(str(aFoundDeeplabcutDataFile)))
                self.cache[aFoundDeeplabcutDataFile] = outEventFileObj
                pass

            # Add the current video file path to the loaded files
            self.loadedDeeplabcutFiles.append(aFoundDeeplabcutDataFile)

            parsedFiles = parsedFiles + 1
            progress_callback.emit(active_deeplabcut_data_file_paths, (parsedFiles*100/numPendingFiles))

        return "Done."
 
    @pyqtSlot(list, object)
    def on_load_deeplabcut_data_files_print_output(self, active_video_paths, s):
        print(s)
        
    @pyqtSlot(list)
    def on_load_deeplabcut_data_files_thread_complete(self, finished_loaded_deeplabcut_data_files):
        print("THREAD on_load_deeplabcut_data_files_thread_complete(...)! {0}".format(str(finished_loaded_deeplabcut_data_files)))
        # The finished_loaded_deeplabcut_data_files are paths that have already been added to self.loadedDeeplabcutFiles. We just need to remove them from self.deeplabcutFilePaths
        for aFinishedVideoFilePath in finished_loaded_deeplabcut_data_files:
            self.deeplabcutFilePaths.remove(aFinishedVideoFilePath)

        self.loadingDeeplabcutDataFilesComplete.emit()




    @pyqtSlot(datetime, datetime)
    def set_start_end_video_file_dates(self, new_start_dates, new_end_dates):
        self.videoStartDates = np.array(new_start_dates)
        self.videoEndDates = np.array(new_end_dates)
        self.reload_on_deeplabcut_paths_changed()


    @pyqtSlot(datetime, datetime, timedelta)
    def on_active_global_timeline_times_changed(self, totalStartTime, totalEndTime, totalDuration):
        # print("ReferenceMarkerManager.on_active_global_timeline_times_changed({0}, {1}, {2})".format(str(totalStartTime), str(totalEndTime), str(totalDuration)))
        # self.totalStartTime = totalStartTime
        # self.totalEndTime = totalEndTime
        # self.totalDuration = totalDuration
        return


