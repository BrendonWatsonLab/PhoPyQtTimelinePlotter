# VideoFilesystemLoadingMixin.py
import sys
from datetime import datetime, timezone, timedelta
from enum import Enum

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool

import cv2

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingQObject

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult, CachedFileSource

from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker
from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker

from pathlib import Path

from app.database.entry_models.db_model import FileParentFolder, StaticFileExtension, VideoFile
from app.filesystem.VideoConversionHelpers import HandbrakeConversionQueue, save_handbrake_conversion_queue

from app.filesystem.VideoFilesystemLoadingMixin import OperationTypes, PendingFilesystemOperation


# from app.filesystem.VideoPreviewThumbnailGeneratingMixin import VideoThumbnail, VideoPreviewThumbnailGenerator

class VideoThumbnail(QObject):
    def __init__(self, frameIndex, thumbsDict, parent=None):
        super().__init__(parent=parent)
        self.frameIndex = frameIndex
        self.thumbsDict = thumbsDict

    def get_frame_index(self):
        return self.frameIndex

    def get_thumbs_dict(self):
        return self.thumbsDict
        
## VideoPreviewThumbnailGenerator: this object tries to find video files in the filesystem and add them to the database if they don't exist
"""
Loads the VideoFiles from the database (cached versions) and then tries to search the filesystem for additional video files.
"""
class VideoPreviewThumbnailGenerator(QObject):

    targetVideoFilePathsUpdated = pyqtSignal()

    generatedThumbnailsUpdated = pyqtSignal()
    thumbnailGenerationComplete = pyqtSignal()


    def __init__(self, videoFilePaths, parent=None):
        super(VideoPreviewThumbnailGenerator, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.cache = dict()
        self.videoFilePaths = videoFilePaths
        self.loadedVideoFiles = []
        self.pending_operation_status = PendingFilesystemOperation(OperationTypes.NoOperation, 0, 0, parent=self)

        # self.reload_on_video_paths_changed()
        
        self.videoThumbnailGeneratorWorker = None
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        if (len(videoFilePaths) > 0):
            self.reload_on_video_paths_changed()
        # self.reload_data()


    def get_cache(self):
        return self.cache

    ## DATABASE Functions:
    def reload_data(self, restricted_video_file_paths=None):
        print("VideoPreviewThumbnailGenerator.reload_data(...)")
        if restricted_video_file_paths is None:
            restricted_video_file_paths = self.videoFilePaths

        self.generate_video_thumbnails(restricted_video_file_paths)

        self.targetVideoFilePathsUpdated.emit()


    # Called to add a new video path to generate thumbnails for
    def add_video_path(self, newVideoFilePath):
        if (newVideoFilePath in self.videoFilePaths):
            print("WARNING: {0} is already in videoFilePaths! Not adding again.".format(str(newVideoFilePath)))
            return False
        
        # If it's in the array of already completed video files, skip it as well
        if (newVideoFilePath in self.loadedVideoFiles):
            print("WARNING: {0} is already in loadedVideoFiles! It's already been processed, so we're not adding it again.".format(str(newVideoFilePath)))
            return False

        # Otherwise we can add it
        self.videoFilePaths.append(newVideoFilePath)
        self.reload_on_video_paths_changed()
        # self.reload_data()


    def reload_on_video_paths_changed(self):
        print("VideoPreviewThumbnailGenerator.reload_on_video_paths_changed(...)")
        if (len(self.videoFilePaths)>0):
            self.generate_video_thumbnails(self.videoFilePaths)
    
        self.targetVideoFilePathsUpdated.emit()



    ## Primary Filesystem Functions

    ## generate_video_thumbnails:
        # Finds the video metadata in a multithreaded way
    def generate_video_thumbnails(self, videoPaths):
        print("VideoPreviewThumbnailGenerator.generate_video_thumbnails(videoPaths: {0})".format(str(videoPaths)))
        # Pass the function to execute
        self.videoThumbnailGeneratorWorker = VideoMetadataWorker(videoPaths, self.on_generate_video_thumbnails_execute_thread) # Any other args, kwargs are passed to the run function
        self.videoThumbnailGeneratorWorker.signals.result.connect(self.on_generate_video_thumbnails_print_output)
        self.videoThumbnailGeneratorWorker.signals.finished.connect(self.on_generate_video_thumbnails_thread_complete)
        self.videoThumbnailGeneratorWorker.signals.progress.connect(self.on_generate_video_thumbnails_progress_fn)
        
        # Execute
        self.threadpool.start(self.videoThumbnailGeneratorWorker) 

    @pyqtSlot(list, int)
    def on_generate_video_thumbnails_progress_fn(self, active_video_paths, n):
        self.pending_operation_status.update(n)
        self.generatedThumbnailsUpdated.emit()
        print("%d%% done" % n)

    def on_generate_video_thumbnails_execute_thread(self, active_video_paths, progress_callback):
        currProgress = 0.0
        parsedFiles = 0
        self.pending_operation_status.restart(OperationTypes.FilesystemThumbnailGeneration, active_video_paths)
        numFilesToGenerateThumbnailsFor = len(active_video_paths)
        for (sub_index, aFoundVideoFile) in enumerate(active_video_paths):
            # Iterate through all found video-files in a given list
            generatedThumbnailObjsList = VideoPreviewThumbnailGenerator.generate_thumbnails_for_video_file(aFoundVideoFile, enable_debug_print=True)
            
            if (not (aFoundVideoFile in self.cache.keys())):
                # Parent doesn't yet exist in cache
                self.cache[aFoundVideoFile] = generatedThumbnailObjsList
            else:
                # Parent already exists
                print("WARNING: video path {0} already exists in the cache. Updating its thumbnail objects list...".format(str(aFoundVideoFile)))
                self.cache[aFoundVideoFile] = generatedThumbnailObjsList
                pass

            # Add the current video file path to the loaded files
            self.loadedVideoFiles.append(aFoundVideoFile)

            parsedFiles = parsedFiles + 1
            progress_callback.emit(active_video_paths, (parsedFiles*100/numFilesToGenerateThumbnailsFor))

        return "Done."
 
    @pyqtSlot(list, object)
    def on_generate_video_thumbnails_print_output(self, active_video_paths, s):
        print(s)
        
    @pyqtSlot(list)
    def on_generate_video_thumbnails_thread_complete(self, finished_video_files):
        print("THREAD on_generate_video_thumbnails_thread_complete(...)! {0}".format(str(finished_video_files)))
        # The finished_video_files are paths that have already been added to self.loadedVideoFiles. We just need to remove them from self.videoFilePaths
        
        for aFinishedVideoFilePath in finished_video_files:
            self.videoFilePaths.remove(aFinishedVideoFilePath)

        # self.loadedVideoFiles.extend(finished_video_files)
        self.thumbnailGenerationComplete.emit()




    @staticmethod
    def generate_thumbnails_for_video_file(activeVideoFilePath, enable_debug_print):
        """Extract frames from the video and creates thumbnails for one of each"""
        # Extract frames from video
        if enable_debug_print:
            print("generate_thumbnails_for_video_file({0})...".format(str(activeVideoFilePath)))

        outputThumbnailObjsList = []
        frames = VideoPreviewThumbnailGenerator.video_to_frames(activeVideoFilePath, enable_debug_print)

        # Generate and save thumbs
        for i in range(len(frames)):
            thumbs = VideoPreviewThumbnailGenerator.image_to_thumbs(frames[i], enable_debug_print)
            currThumbnailObj = VideoThumbnail(i, thumbs)
            outputThumbnailObjsList.append(currThumbnailObj)

            # os.makedirs('frames/%d' % i)
            # for k, v in thumb.items():
            #     # cv2.imencode()
            #     cv2.imwrite('frames/%d/%s.png' % (i, k), v)

        return outputThumbnailObjsList



    @staticmethod
    def video_to_frames(video_filename, enable_debug_print):
        """Extract frames from video"""
        if enable_debug_print:
            print("video_to_frames({0})...".format(str(video_filename)))
        cap = cv2.VideoCapture(video_filename)
        video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        frames = []
        if cap.isOpened() and video_length > 0:
            frame_ids = [0]
            if video_length >= 4:
                frame_ids = [0, 
                            round(video_length * 0.25), 
                            round(video_length * 0.5),
                            round(video_length * 0.75),
                            video_length - 1]
            count = 0
            success, image = cap.read()
            while success:
                if count in frame_ids:
                    frames.append(image)
                success, image = cap.read()
                count += 1

        if enable_debug_print:
            print("done. ({0} frames extracted)...".format(str(len(frames))))
        return frames

    @staticmethod
    def image_to_thumbs(img, enable_debug_print):
        """Create thumbs from image"""
        if enable_debug_print:
            print("image_to_thumbs(...)...")
        height, width, channels = img.shape
        thumbs = {"original": img}
        sizes = [640, 320, 160]
        for size in sizes:
            if (width >= size):
                r = (size + 0.0) / width
                max_size = (size, int(height * r))
                thumbs[str(size)] = cv2.resize(img, max_size, interpolation=cv2.INTER_AREA)

        if enable_debug_print:
            print("done.")
        return thumbs