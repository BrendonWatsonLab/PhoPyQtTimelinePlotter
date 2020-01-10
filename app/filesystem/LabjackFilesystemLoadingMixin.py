# LabjackFilesystemLoadingMixin.py
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


# from pyqtgraph import ProgressDialog
# import pyqtgraph as pg
# class ProgressDialogDisplayingMixin(QObject):

#     def __init__(self, filePath, parent=None):
#         super().__init__(parent=parent)

#         with ProgressDialog("Processing..", 0, 100, cancelText='Cancel', parent=self, busyCursor=True) as dlg:
#             # do stuff
#             self.get_labjack_data_files_loader().add_labjack_file_path(importFilePath)
#             # dlg.setValue(i)   ## could also use dlg += 1
#             dlg += 1
#             if dlg.wasCanceled():
#                 raise Exception("Processing canceled by user")




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

        self.labjackFilesystemWorker = None
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(2)
        
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        
        self.reload_on_labjack_paths_changed()
        
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
    # @pyqtSlot(list, int)
    # def on_load_labjack_data_files_progress_fn(self, active_labjack_data_file_paths, n):     
    #     self.pending_operation_status.update(n)
    #     self.labjackDataFileLoaded.emit()
    #     print("%d%% done" % n)

    @pyqtSlot(list, int)
    def on_load_labjack_data_files_progress_fn(self, latest_labjack_file_result_list, n):
        aFoundLabjackDataFile = latest_labjack_file_result_list[0] # The last loaded URL
        outEventFileObj = latest_labjack_file_result_list[1] # outEventFileObj: LabjackEventFile type object
        print('on_load_labjack_data_files_progress_fn(..., n: {}): file: {}'.format(str(n), str(aFoundLabjackDataFile)))

        # Update our cache
        if (not (aFoundLabjackDataFile in self.cache.keys())):
            print('Creating new cache entry for {}...'.format(str(aFoundLabjackDataFile)))
            # Parent doesn't yet exist in cache
            self.cache[aFoundLabjackDataFile] = outEventFileObj
        else:
            # Parent already exists
            print("WARNING: labjack file path {} already exists in the cache. Updating its values...".format(str(aFoundLabjackDataFile)))
            self.cache[aFoundLabjackDataFile] = outEventFileObj
            pass

        # Add the current video file path to the loaded files
        self.loadedLabjackFiles.append(aFoundLabjackDataFile)
        
        # updated!
        self.pending_operation_status.update(n)
        self.labjackDataFileLoaded.emit()
        # print("%d%% done" % n)


# LabjackEventFile

    """
    The main execution function
    """
    def on_load_labjack_data_files_execute_thread(self, active_labjack_data_file_paths, progress_callback):

        # should_filter_for_invalid_events = True
        should_filter_for_invalid_events = False
        
        currProgress = 0.0
        parsedFiles = 0
        numPendingFiles = len(active_labjack_data_file_paths)
        self.pending_operation_status.restart(OperationTypes.FilesystemLabjackFileLoad, numPendingFiles)

        new_cache = dict()
        
        # active_cache = self.cache
        active_cache = new_cache
        # Loop through all the labjack data file paths and parse the files into a LabjackEventFile object.
        for (sub_index, aFoundLabjackDataFile) in enumerate(active_labjack_data_file_paths):

            # LabjackEventFile: this serves as a container to hold the loaded events
            outEventFileObj = LabjackEventFile(aFoundLabjackDataFile)

            # Call the static "loadLabjackEventsFile(...) function:

            # (dateTimes, onesEventFormatDataArray, variableData, labjackEvents) = LabjackFilesystemLoader.loadLabjackFiles(aFoundLabjackDataFile, self.videoStartDates, self.videoEndDates, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
            # (dateTimes, onesEventFormatDataArray, variableData, labjackEvents) = LabjackFilesystemLoader.loadLabjackEventsFile(aFoundLabjackDataFile, self.videoStartDates, self.videoEndDates, shouldLimitEventsToVideoDates=False, usePhoServerFormat=True, phoServerFormatIsStdOut=False)
            (dateTimes, labjackEventContainers, phoServerFormatArgs) = LabjackFilesystemLoader.loadLabjackEventsFile(aFoundLabjackDataFile, self.videoStartDates, self.videoEndDates, shouldLimitEventsToVideoDates=False, usePhoServerFormat=True, phoServerFormatIsStdOut=False, should_filter_for_invalid_events=should_filter_for_invalid_events)

            print('Loading complete... setting loaded values')
            # Cache the loaded values into the LabjackEventFile object.
            # outEventFileObj.set_loaded_values(dateTimes, [], [], labjackEventContainers, phoServerFormatArgs)
            outEventFileObj.set_loaded_values(dateTimes, [], [], labjackEventContainers, None)
            print('done updating cache...')
            
            if (not (aFoundLabjackDataFile in active_cache.keys())):
                # print('Creating new cache entry for {}...'.format(str(aFoundLabjackDataFile)))
                # Parent doesn't yet exist in cache
                active_cache[aFoundLabjackDataFile] = outEventFileObj
            else:
                # Parent already exists
                print("WARNING: labjack file path {} already exists in the temporary cache. Updating its values...".format(str(aFoundLabjackDataFile)))
                active_cache[aFoundLabjackDataFile] = outEventFileObj
                pass


            parsedFiles = parsedFiles + 1
            # progress_callback.emit(active_labjack_data_file_paths, (parsedFiles*100/numPendingFiles))
            progress_callback.emit([aFoundLabjackDataFile, outEventFileObj], (parsedFiles*100/numPendingFiles))

        # return "Done."
        # Returns the cache when done
        return new_cache
 
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


    """ loadLabjackEventsFile(...): new.
        labjackEventRecords: a sorted list of FilesystemLabjackEvent_Record type objects for all variable types
    """
    @staticmethod
    def loadLabjackEventsFile(labjackFilePath, videoDates, videoEndDates, shouldLimitEventsToVideoDates=True, limitedVariablesToCreateEventsFor=None, usePhoServerFormat=False, phoServerFormatIsStdOut=True, should_filter_for_invalid_events=True):
        ## Load the Labjack events data from an exported MATLAB file
        # If shouldLimitEventsToVideoDates is True then only events that fall between the earliest video start date and the latest video finish date are included
        # If shouldLimitEventsToVariables is not None, then only events that are of type of the variable with the name in the array are included
        ## TODO: shouldLimitEventsToVideoDates should also affect the returned dateTimes, dataArray, etc.
        (dateTimes, onesEventFormatDataArray, phoServerFormatArgs) = LabjackEventsLoader.loadLabjackEventsFile_loadFromFile(labjackFilePath, usePhoServerFormat, phoServerFormatIsStdOut)

        ## Pre-process the data
        if limitedVariablesToCreateEventsFor is not None:
            active_labjack_variable_names = limitedVariablesToCreateEventsFor

        else:
            # Otherwise load for all variables
            active_labjack_variable_names = LabjackEventsLoader.labjack_variable_names

        numVariables = len(active_labjack_variable_names)

        if ((videoDates is not None) and (len(videoDates) > 0)):
            earliestVideoTime = videoDates.min()
        else:
            earliestVideoTime = datetime.min

        if ((videoEndDates is not None) and (len(videoEndDates) > 0)):
            latestVideoTime = videoEndDates.max()
        else:
            latestVideoTime = datetime.max

        

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

            # Acumulate records one variable at a time
            labjackVariableSpecificRecords = []
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
                    # Create a new record object
                    ## TODO: should this have a different parent?
                    currRecord = FilesystemLabjackEvent_Record(anActiveTimestamp.replace(tzinfo=None), None, currVariableName, currVariableColor, currExtendedInfoDict, parent=None)
                    labjackVariableSpecificRecords.append(currRecord)


            # Append the variable-specific events to the master list of events
            labjackEventRecords.extend(labjackVariableSpecificRecords)
            # Add the value-dict for this variable to the 'variableData' list
            variableData.append({'timestamps': activeTimestamps, 'values': activeValues, 'videoIndicies': activeVideoIndicies, 'variableSpecificRecords': labjackVariableSpecificRecords})


        # Sort events by timestamp
        try: import operator
        except ImportError: keyfun = lambda x: x.start_date  # use a lambda if no operator module
        else: keyfun = operator.attrgetter("start_date")  # use operator since it's faster than lambda
        labjackEventRecords = sorted(labjackEventRecords, key=keyfun)

        # Be sure to convert into a numpy array AFTER sorting
        labjackEventRecords = np.array(labjackEventRecords)
        # labjackEvents = np.array(labjackEvents)

        print('    done. {} total labjackEvents loaded'.format(str(len(labjackEventRecords))))
        # 'Pre-Filter:' dateTimes.size, labjackEventRecords.size, onesEventFormatDataArray.shape
        # 'Pre-Filter:' 76117, 41189, (76117, 9)
        """
        dateTimes: ndarray, shape (76117,)
        labjackEventRecords: ndarray, shape (41189,)
        onesEventFormatDataArray: ndarray, shape (76117, 9)
        variableData: a list of 8 dicts defined by: {'timestamps': ndarray, 'values': ndarray, 'videoIndicies': ndarray, 'variableSpecificRecords': list} where each dict in the list corresponds to a variable with that index
            - all fields have same shape (1433,)
            - 'variableSpecificRecords' is a list of length 1433
            
        variable-specific lengths (in this file): (1433, 6717, 1496, 12422, 772, 3223, 851, 14275)
        """
        if should_filter_for_invalid_events:
            print('Filtering for invalid events...')
            ### Post-processing to detect erronious events, only for food2
            dateTimes, onesEventFormatDataArray, variableData, labjackEventRecords, phoServerFormatArgs = LabjackEventsLoader.filter_invalid_events(dateTimes, onesEventFormatDataArray, variableData, labjackEventRecords, phoServerFormatArgs=phoServerFormatArgs)
            print('Post-filtering: {} events remain'.format(str(len(labjackEventRecords))))
            print('    done.')
        else:
            print('Skipping filtering...')

        """ Post-filtering:
        dateTimes: ndarray, shape (68574,)
        labjackEventRecords: ndarray, shape (33646,)
        onesEventFormatDataArray: ndarray, shape (68574, 9)
        variableData: counts match those printed in filter_invalid_events function
        """

        """
        converts the variableData list of dicts to a proper Pandas dataframe
        """
        def get_variables_as_dict_of_dataframes(variableData, active_labjack_variable_names):
            # Convert to dataframe:
            variableDataFramesDict = dict()
            # Loop through all variables and build a dataframe for each variable data in variableData
                    # for aVariableIndex in range(0, numVariables):
            for (aVariableIndex, currVariableName) in enumerate(active_labjack_variable_names):
                # currVariableName = active_labjack_variable_names[aVariableIndex]
                variableDataFramesDict[currVariableName] = pd.DataFrame.from_dict(variableData[aVariableIndex])

            return variableDataFramesDict

        def get_dict_of_dataframes_as_dataframe(variableDataFramesDict):
            return pd.concat(variableDataFramesDict)
            # return pd.concat(variableDataFramesDict, keys=['s1', 's2'],  names=['Series name', 'Row ID'])


        # """ Export Dataframe to file:
        # Writing dataframe to file data/output/LabjackDataExport/output_dataframe_1-9-2020...
        # C:\Users\halechr\repo\PhoPyQtTimelinePlotter\app\filesystem\LabjackFilesystemLoadingMixin.py:257: PerformanceWarning:
        # your performance may suffer as PyTables will pickle object types that it cannot
        # map directly to c-types [inferred_type->mixed-integer,key->block2_values] [items->['videoIndicies', 'variableSpecificRecords']]
        # """

        out_dataframe_export_parent_path = Path('data/output/LabjackDataExport/')
        out_dataframe_export_path_basic = out_dataframe_export_parent_path.joinpath('output_dataframe_1-9-2020_basic_store.h5') # Used for basic objects
        out_dataframe_export_path_pandas = out_dataframe_export_parent_path.joinpath('output_dataframe_1-9-2020_pandas_store.h5') # Used for pandas Dataframe and Series objects

        print('Converting variableData to dict of Pandas Dataframes...')
        out_dict_of_df = get_variables_as_dict_of_dataframes(variableData, active_labjack_variable_names)


        # # Write basic variables:
        # print('Writing dataframe to file {}...'.format(str(out_dataframe_export_path_basic)))
        # store_basic = pd.HDFStore(out_dataframe_export_path_basic)
        # # store_basic['variableData'] = variableData
        # # store_basic['active_labjack_variable_names'] = active_labjack_variable_names
        # # store_basic['variables_dict_of_dataframes'] = out_dict_of_df
        # store_basic.close()
        # print('    done writing basic variables to HDF file.')

        print('Converting variableData to Pandas Dataframe...')
        # out_df = get_variables_as_dataframe(variableData, active_labjack_variable_names)
        out_df = get_dict_of_dataframes_as_dataframe(out_dict_of_df)
        out_series = pd.Series(out_dict_of_df)

        # out_df.to_json(orient='split')
        print('Writing dataframe to file {}...'.format(str(out_dataframe_export_path_pandas)))
        # out_df.to_pickle(out_dataframe_export_path)
        store_pandas = pd.HDFStore(out_dataframe_export_path_pandas)
        # store.get_storer('df').attrs.my_attribute = dict(A = 10)
        store_pandas['variables_dataframe'] = out_df
        store_pandas['variables_series_of_dataframes'] = out_series
        store_pandas.close()
        
        print('    done writing pandas variables to HDF file.')
        # for (aVariableIndex, aVariableData) in enumerate(variableData):
        #     aVariableData['']
            

        # Build the corresponding GUI objects
        print('building container array...')
        ## TODO: defer until needed? Some might be filtered out anyway.
        built_model_view_container_array = []
        for (index, aRecord) in enumerate(labjackEventRecords):
            aGuiView = aRecord.get_gui_view(aRecord, parent=None)
            aModelViewContainer = ModelViewContainer(aRecord, aGuiView)
            built_model_view_container_array.append(aModelViewContainer)

        # labjackEvents = [FilesystemLabjackEvent_Record.get_gui_view(aRecord, parent=None) for aRecord in labjackEventRecords]
        print('done building container array.')

        # return (dateTimes, onesEventFormatDataArray, variableData, labjackEvents)
        return (dateTimes, built_model_view_container_array, phoServerFormatArgs)
