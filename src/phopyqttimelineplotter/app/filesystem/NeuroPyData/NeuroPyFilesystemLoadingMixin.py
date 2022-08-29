# NeuroPyFilesystemLoadingMixin.py
import sys

# import pickle
# import cPickle
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from phopyqttimelineplotter.app.filesystem.FilesystemOperations import (
    OperationTypes,
    PendingFilesystemOperation,
)
from phopyqttimelineplotter.app.filesystem.FilesystemRecordBase import (
    FilesystemDataEvent_Record,
    discover_data_files,
)
from phopyqttimelineplotter.app.filesystem.GeneralData.BaseDataFileFilesystemLoadingMixin import (
    BaseDataEventFile,
    BaseDataFilesystemLoader,
)
from phopyqttimelineplotter.app.filesystem.VideoUtils import (
    CachedFileSource,
    FoundVideoFileResult,
    VideoParsedResults,
    findVideoFiles,
)
from phopyqttimelineplotter.app.filesystem.Workers.FileMetadataWorkers import FileMetadataWorker
from phopyqttimelineplotter.app.filesystem.Workers.VideoFilesystemWorkers import VideoFilesystemWorker

from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen

import silx.io
from silx.io.url import DataUrl # DataUrl

from phopyqttimelineplotter.GUI.Model.ModelViewContainer import ModelViewContainer
from phopyqttimelineplotter.GUI.UI.AbstractDatabaseAccessingWidgets import (
    AbstractDatabaseAccessingQObject,
)

# from phopyqttimelineplotter.app.filesystem.NeuroPyData.NeuroPyEventsLoader import NeuroPyEventsLoader, PhoServerFormatArgs

# from phopyqttimelineplotter.GUI.Model.Events.PhoDurationEvent import PhoDurationEvent

# from phopyqttimelineplotter.app.filesystem.NeuroPyData.NeuroPyFilesystemLoadingMixin import NeuroPyEventFile, NeuroPyFilesystemLoader


class NeuroPyEventFile(BaseDataEventFile):
    """NeuroPyEventFile: a single imported data file containing one or more labjack events."""

    def __init__(self, filePath, parent=None):
        super().__init__(filePath, parent=parent)
        # Custom variables
        # self.onesEventFormatDataArray = []

    # def set_loaded_values(self, dateTimes, variableData, labjackEventsContainerArray, phoServerFormatArgs, onesEventFormatDataArray):
    #     BaseDataEventFile.set_loaded_values(self, dateTimes, onesEventFormatDataArray, variableData, labjackEventsContainerArray, phoServerFormatArgs)
    #     self.onesEventFormatDataArray = onesEventFormatDataArray # set the custom values


class NeuroPyFilesystemLoader(BaseDataFilesystemLoader):
    """NeuroPyFilesystemLoader: this object tries to find NeuroPy-exported data files in the filesystem and make them accessible in memory
    Loads the NeuroPy event files

    Inherited Signals:
        targetDataFilePathsUpdated = pyqtSignal()
        dataFileLoaded = pyqtSignal()
        loadingDataFilesComplete = pyqtSignal()

    """
    variable_names = [
        "x",
        "y",
        "z",
    ]
    variable_colors = [
        "aqua",
        "crimson",
        "blue",
    ]
    variable_indicies = [0, 1, 2]
    
    # Derived Dictionaries
    variable_colors_dict = dict( zip(variable_names, variable_colors) )
    variable_indicies_dict = dict( zip(variable_names, variable_indicies) )
    
    
    def __init__(self, dataFilePaths, parent=None):
        super(NeuroPyFilesystemLoader, self).__init__( dataFilePaths, parent=parent )  # Call the inherited classes __init__ method

    def on_load_data_files_execute_thread(self, active_data_file_paths, progress_callback):
        """
        The main execution function - overriden by specific file types to perform the loading action
        TODO: Implement for NeuroPy .h5 and .npz data

        """
        should_filter_for_invalid_events = True
        # should_filter_for_invalid_events = False

        currProgress = 0.0
        parsedFiles = 0
        numPendingFiles = len(active_data_file_paths)
        self.pending_operation_status.restart( OperationTypes.FilesystemDataFileLoad, numPendingFiles )

        new_cache = dict()

        # active_cache = self.cache
        active_cache = new_cache
        # Loop through all the labjack data file paths and parse the files into a NeuroPyEventFile object.
        for (sub_index, aFoundNeuroPyDataFile) in enumerate(active_data_file_paths):

            # NeuroPyEventFile: this serves as a container to hold the loaded events
            outEventFileObj = NeuroPyEventFile(aFoundNeuroPyDataFile)

            # Call the static "loadNeuroPyEventsFile(...) function:
            (dateTimes, activeValues, activeLoadedDataValuesDict) = NeuroPyFilesystemLoader.loadSilxDataSelectionDict(
                aFoundNeuroPyDataFile,
                self.videoStartDates,
                self.videoEndDates,
                shouldLimitEventsToValidBoundDates=False,
            )
            print("Loading complete... setting loaded values")
            # Cache the loaded values into the NeuroPyEventFile object.
            outEventFileObj.set_loaded_values(
                dateTimes, [], labjackEventContainers, None
            )
            print("done updating cache...")

            if not (aFoundNeuroPyDataFile in active_cache.keys()):
                # print('Creating new cache entry for {}...'.format(str(aFoundNeuroPyDataFile)))
                # Parent doesn't yet exist in cache
                active_cache[aFoundNeuroPyDataFile] = outEventFileObj
            else:
                # Parent already exists
                print( f"WARNING: neuropy file path {str(aFoundNeuroPyDataFile)} already exists in the temporary cache. Updating its values..." )
                active_cache[aFoundNeuroPyDataFile] = outEventFileObj
                pass

            parsedFiles = parsedFiles + 1
            progress_callback.emit( [aFoundNeuroPyDataFile, outEventFileObj], (parsedFiles * 100 / numPendingFiles), )

        # return "Done."
        # Returns the cache when done
        return new_cache

    ## Static Methods:

    """ loadNeuroPyEventsFile(...): new.
        labjackEventRecords: a sorted list of FilesystemDataEvent_Record type objects for all variable types
    """
    


    @classmethod
    def loadSilxDataSelectionDict(cls,
        h5DataSelectionDict,
        earliestValidTime,
        latestValidTime,
        shouldLimitEventsToValidBoundDates=True,
        limitedVariablesToCreateEventsFor=None):
        """Load the NeuroPy events data from an exported MATLAB file
        # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
        # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
        ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
        """
        # raise NotImplementedError

        ## Pre-process the data
        if limitedVariablesToCreateEventsFor is not None:
            active_variable_names = limitedVariablesToCreateEventsFor

        else:
            # Otherwise load for all variables
            active_variable_names = list(h5DataSelectionDict.keys())

        activeLoadedDataValuesDict = {var_name:None for var_name in active_variable_names}
        
        numVariables = len(active_variable_names)

        ## Iterate through the event variables and pre-process them
        variableData = []
        # dataEventRecords = []
        # labjackEvents = []
        # Can't check for invalid events in here because we do it variable by variable.
        for variableIndex in range(0, numVariables):
            currVariableName = active_variable_names[variableIndex]
            currVariableDataUrl = h5DataSelectionDict[currVariableName]
            assert currVariableDataUrl is not None
            assert isinstance(currVariableDataUrl, DataUrl)
            
            ## Here we actually load the values:
            currVariableDataValues = silx.io.get_data(currVariableDataUrl)
            activeLoadedDataValuesDict[currVariableName] = currVariableDataValues
            
            # dataArrayVariableIndex = cls.variable_indicies_dict[currVariableName]
            # currVariableDataValues = onesEventFormatDataArray[:, dataArrayVariableIndex]
            # currVariableColorTuple = mcolors.to_rgb(cls.variable_colors_dict[currVariableName])
            # currVariableColor = QColor(
            #     int(255.0 * currVariableColorTuple[0]),
            #     int(255.0 * currVariableColorTuple[1]),
            #     int(255.0 * currVariableColorTuple[2]),
            # )

            # # Find the non-zero entries for the current variable
            # nonZeroEntries = np.nonzero(currVariableDataValues)
            # activeValues = currVariableDataValues[
            #     nonZeroEntries
            # ]  # This is just all ones for 0/1 array
            # activeTimestamps = dateTimes[nonZeroEntries]

            # # Acumulate records one variable at a time
            # dataVariableSpecificRecords = []
            # ## Find times within video ranges:
            # # activeVideoIndicies: contains an int index or None for each timestamp to indicate which video (if any) the timestamp occurred within
            
            # # currExtendedInfoDict = {
            # #     "event_type": NeuroPyEventsLoader.labjack_variable_event_type[ dataArrayVariableIndex ],
            # #     "dispense_type": NeuroPyEventsLoader.labjack_variable_event_type[ dataArrayVariableIndex ],
            # #     "port": NeuroPyEventsLoader.labjack_variable_port_location[ dataArrayVariableIndex ],
            # # }
            # # # Create a new record object
            # # ## TODO: should this have a different parent?
            # # currRecord = FilesystemDataEvent_Record(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict, parent=None, )
            # # dataVariableSpecificRecords.append(currRecord)

            # # Append the variable-specific events to the master list of events
            # dataEventRecords.extend(dataVariableSpecificRecords)
            # # Add the value-dict for this variable to the 'variableData' list
            # variableData.append(
            #     {
            #         "timestamps": activeTimestamps,
            #         "values": activeValues,
            #         "variableSpecificRecords": dataVariableSpecificRecords,
            #     }
            # )

        dateTimes = activeLoadedDataValuesDict['t'] # get the timestamps # TODO: convert to datetimes
        activeValues = list([vals for key, vals in activeLoadedDataValuesDict.items() if key != 't']) #ideally flattened non-timestamp values (like 'x', 'y')
        return (dateTimes, activeValues, activeLoadedDataValuesDict)
