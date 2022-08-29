# FilesystemWorkersBase.py
import os, time, traceback, sys

from datetime import datetime, timezone, timedelta
from pathlib import Path
import fnmatch
import re
import subprocess
import json # Used to decode ffprobe output

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QObject, QEvent, pyqtSignal, pyqtSlot, QRunnable


## IMPORT:
# from phopyqttimelineplotter.app.filesystem.Workers.VideoFilesystemWorkers import FilesystemWorkersBase, FilesystemWorkersBaseSignals


# https://doc.qt.io/archives/qq/qq27-responsive-guis.html#solvingaproblemstepbystep


## FilesystemWorkersBase
class FilesystemWorkersBaseSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    
    Historical: Renamed from `VideoWorkersBaseSignals` to `FilesystemWorkersBaseSignals` since it was discovered to be used in non video specific operations (like finding Labjack data files)
    
    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress 

    '''
    finished = pyqtSignal(list)
    error = pyqtSignal(list, tuple)
    result = pyqtSignal(list, object)
    progress = pyqtSignal(list, int)


class FilesystemWorkersBase(QRunnable):
    '''
    Worker thread
    
    Historical: Renamed from `VideoWorkersBase` to `FilesystemWorkersBase` since it was discovered to be used in non video specific operations (like finding Labjack data files)
    

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, search_paths, fn, *args, **kwargs):
        super(FilesystemWorkersBase, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.search_paths = search_paths
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = FilesystemWorkersBaseSignals()    

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress        

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(self.search_paths, *self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit(self.search_paths, (exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(self.search_paths, result)  # Return the result of the processing
        finally:
            # self.signals.finished.emit()  # Done
            self.signals.finished.emit(self.search_paths)  # Done
        

