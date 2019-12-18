# VideoFilesystemLoadingMixin.py
import sys
from datetime import datetime, timezone, timedelta
from enum import Enum

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool

import subprocess
import cv2

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingQObject

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult, CachedFileSource

from app.filesystem.VideoMetadataWorkers import VideoMetadataWorker
from app.filesystem.VideoFilesystemWorkers import VideoFilesystemWorker

from pathlib import Path

from app.database.entry_models.db_model import FileParentFolder, StaticFileExtension, VideoFile
from app.filesystem.VideoConversionHelpers import HandbrakeConversionQueue, save_handbrake_conversion_queue

from app.filesystem.FilesystemOperations import OperationTypes, PendingFilesystemOperation

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

    # All video items
    thumbnailGenerationComplete = pyqtSignal()


    # Single Video Event Item:
    videoThumbnailGenerationComplete = pyqtSignal(str, list) # filename, [VideoThumbnail]



    def __init__(self, videoFilePaths, thumbnailSizes = [160, 80, 40], parent=None):
        super(VideoPreviewThumbnailGenerator, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.cache = dict()
        self.videoFilePaths = videoFilePaths
        self.loadedVideoFiles = []
        self.desiredThumbnailSizes = thumbnailSizes
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
        numFilesToGenerateThumbnailsFor = len(active_video_paths)
        self.pending_operation_status.restart(OperationTypes.FilesystemThumbnailGeneration, numFilesToGenerateThumbnailsFor)

        for (sub_index, aFoundVideoFile) in enumerate(active_video_paths):
            # Iterate through all found video-files in a given list (a list of VideoThumbnail objects: [VideoThumbnail])
            generatedThumbnailObjsList = VideoPreviewThumbnailGenerator.generate_thumbnails_for_video_file(aFoundVideoFile, self.desiredThumbnailSizes, enable_debug_print=True)
            
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
            self.videoThumbnailGenerationComplete.emit(aFoundVideoFile, generatedThumbnailObjsList)

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
    def generate_thumbnails_for_video_file(activeVideoFilePath, thumbnailSizes, enable_debug_print=False):
        """Extract frames from the video and creates thumbnails for one of each"""
        # Extract frames from video
        if enable_debug_print:
            print("generate_thumbnails_for_video_file({0})...".format(str(activeVideoFilePath)))

        outputThumbnailObjsList = []
        frames = VideoPreviewThumbnailGenerator.video_to_frames(activeVideoFilePath, enable_debug_print)

        # Generate and save thumbs
        for i in range(len(frames)):
            thumbs = VideoPreviewThumbnailGenerator.image_to_thumbs(frames[i], thumbnailSizes, enable_debug_print)
            currThumbnailObj = VideoThumbnail(i, thumbs)
            outputThumbnailObjsList.append(currThumbnailObj)

            # os.makedirs('frames/%d' % i)
            # for k, v in thumb.items():
            #     # cv2.imencode()
            #     cv2.imwrite('frames/%d/%s.png' % (i, k), v)

        return outputThumbnailObjsList



    """ video_to_desired_frames(...): 
    TODO: currently hardcoded to return either 1 (the first) or 5 frames.

    """
    @staticmethod
    def video_to_desired_frames(video_filename, desired_frame_indexes, enable_debug_print, use_OpenCV_method=True):
        """Extract frames from video"""
        if enable_debug_print:
            print("video_to_desired_frames({0})...".format(str(video_filename)))

        frames = []

        if use_OpenCV_method:
            if enable_debug_print:
                print("    video_to_desired_frames(...): using OpenCV method...")
            cap = cv2.VideoCapture(video_filename)
            video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1

            if cap.isOpened() and video_length > 0:
                frame_ids = [0]
                # Check if desired_frame_indexes is None. If it is, use the default frames. Otherwise, use the user's specified frames
                if desired_frame_indexes is None:
                    frame_ids = [0]
                    if video_length >= 4:
                        frame_ids = [0,
                                    round(video_length * 0.25),
                                    round(video_length * 0.5),
                                    round(video_length * 0.75),
                                    video_length - 1]
                else:
                    # Non-None desired_frame_indicies:
                    for aDesiredFrameID in desired_frame_indexes:
                        if (0 <= aDesiredFrameID < video_length):
                            frame_ids.append(aDesiredFrameID)
                        elif (aDesiredFrameID >= video_length):
                            # desired index is too big
                            frame_ids.append(video_length - 1) # Get the last frame
                        elif (aDesiredFrameID < 0):
                            frame_ids.append(0) # Get the first frame
                        else:
                            print("WARNING: this shouldn't happen!")

                count = 0
                for aFrameNumber in frame_ids:
                    #The first argument of cap.set(), number 2 defines that parameter for setting the frame selection.
                    #Number 2 defines flag CV_CAP_PROP_POS_FRAMES which is a 0-based index of the frame to be decoded/captured next.
                    #The second argument defines the frame number in range 0.0-1.0
                    cap.set(1, aFrameNumber)
                    success, image = cap.read()
                    if success:
                        print("frame_number[{0}]: SUCCESS!".format(str(aFrameNumber)))
                        # Set grayscale colorspace for the frame.
                        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                        # Cut the video extension to have the name of the video
                        # my_video_name = video_filename.split(".")[0]
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        frames.append(image)
                        count += 1
                    else:
                        print("frame_number[{0}] failed".format(str(aFrameNumber)))
                        continue

            # When everything done, release the capture (from https://stackoverflow.com/questions/33650974/opencv-python-read-specific-frame-using-videocapture) not sure if I need to do this.
            cap.release()
            cv2.destroyAllWindows()

        else:
            # Use FFMPEG method:
            print("    video_to_desired_frames(...): using FFMPEG method...")
            """
            -ss: the start time
            -vframes:
            """
            img_output_path = '/data/output/temp.jpg'
            subprocess.call(['ffmpeg', '-i', video_filename, '-ss', '00:00:00.000', '-vframes:1', img_output_path])
            # TODO: Read them back in

        if enable_debug_print:
            print("done. ({0} frames extracted)...".format(str(len(frames))))

        return frames




    """ video_to_frames(...): 
    TODO: currently hardcoded to return either 1 (the first) or 5 frames.

    """
    @staticmethod
    def video_to_frames(video_filename, enable_debug_print, use_OpenCV_method=True):
        """Extract frames from video"""
        return VideoPreviewThumbnailGenerator.video_to_desired_frames(video_filename, None, enable_debug_print, use_OpenCV_method)


    """ image_to_thumbs(img, ...): converts an image to a dictionary of different sized thumbnails
        img: the image to compute the thumbnails for
        thumbnailSizes: [int]: an array of the different thumbnail sizes to generate (in pixels)
    """
    @staticmethod
    def image_to_thumbs(img, thumbnailSizes, enable_debug_print= False):
        """Create thumbs from image"""
        if enable_debug_print:
            print("image_to_thumbs(...)...")
        height, width, channels = img.shape
        bytesPerLine = channels * width
        qImg = QtGui.QImage(img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)

        # thumbs = {"original": img}
        thumbs = {"original": qImg}
        # sizes = [640, 320, 160]
        # sizes = [160, 80, 40]
        for size in thumbnailSizes:
            if (width >= size):
                r = (size + 0.0) / width
                max_size = (size, int(height * r))
                # thumbs[str(size)] = cv2.resize(img, max_size, interpolation=cv2.INTER_AREA)
                curr_raw_image = cv2.resize(img, max_size, interpolation=cv2.INTER_AREA)
                curr_height, curr_width, curr_channels = curr_raw_image.shape
                curr_bytesPerLine = curr_channels * curr_width
                curr_q_img = QtGui.QImage(curr_raw_image.data, curr_width, curr_height, curr_bytesPerLine, QtGui.QImage.Format_RGB888)
                thumbs[str(size)] = curr_q_img


        if enable_debug_print:
            print("done.")
        return thumbs