# VideoWorkersBase.py
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
# from app.filesystem.Workers.VideoFilesystemWorkers import VideoWorkersBase, VideoWorkersBaseSignals


# https://doc.qt.io/archives/qq/qq27-responsive-guis.html#solvingaproblemstepbystep


## VideoWorkersBase
class VideoWorkersBaseSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

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


class VideoWorkersBase(QRunnable):
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
        super(VideoWorkersBase, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.search_paths = search_paths
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = VideoWorkersBaseSignals()    

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
        

