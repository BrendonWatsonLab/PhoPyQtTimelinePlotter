import os, time, traceback, sys

from datetime import datetime, timezone, timedelta
from pathlib import Path
import fnmatch
import re
import subprocess
import json # Used to decode ffprobe output

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QObject, QEvent, pyqtSignal, pyqtSlot, QRunnable

from app.filesystem.Workers.FilesystemWorkersBase import FilesystemWorkersBase

## IMPORT:

## VideoMetadataWorker
# class VideoMetadataWorkerSignals(QObject):
#     '''
#     Defines the signals available from a running worker thread.

#     Supported signals are:

#     finished
#         No data
    
#     error
#         `tuple` (exctype, value, traceback.format_exc() )
    
#     result
#         `object` data returned from processing, anything

#     progress
#         `int` indicating % progress 

#     '''
#     finished = pyqtSignal()
#     error = pyqtSignal(tuple)
#     result = pyqtSignal(object)
#     progress = pyqtSignal(int)


class FileMetadataWorker(FilesystemWorkersBase):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, search_paths, fn, *args, **kwargs):
        super(FileMetadataWorker, self).__init__(search_paths, fn, *args, **kwargs)

        # Store constructor arguments (re-used for processing)
        # self.fn = fn
        # self.args = args
        # self.kwargs = kwargs
        # self.signals = VideoMetadataWorkerSignals()    

        # # Add the callback to our kwargs
        # self.kwargs['progress_callback'] = self.signals.progress        

    # @pyqtSlot()
    # def run(self):
    #     '''
    #     Initialise the runner function with passed args, kwargs.
    #     '''
        
    #     # Retrieve args/kwargs here; and fire processing using them
    #     try:
    #         result = self.fn(*self.args, **self.kwargs)
    #     except:
    #         traceback.print_exc()
    #         exctype, value = sys.exc_info()[:2]
    #         self.signals.error.emit((exctype, value, traceback.format_exc()))
    #     else:
    #         self.signals.result.emit(result)  # Return the result of the processing
    #     finally:
    #         self.signals.finished.emit()  # Done
        

