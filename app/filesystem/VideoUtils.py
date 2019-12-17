## Video Parsing Utils (from filesystem)
# VideoUtils.py

# Inspired by:
# https://stackoverflow.com/questions/47454317/getting-video-properties-with-python-without-calling-external-software

import os, time, traceback, sys

from datetime import datetime, timezone, timedelta
from pathlib import Path
import fnmatch
import re
import subprocess
import json # Used to decode ffprobe output
from enum import Enum

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog
# from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QStandardItemModel
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QRunnable

# # Used to get the video file metadata
# from hachoir.parser import createParser
# from hachoir.metadata import extractMetadata

## IMPORT:
# from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult
# from app.filesystem.VideoUtils import findDeeplabCutProducedOutputFiles, FoundDeeplabcutOutputFileResult

# Basler emulation style:
videoFileNameParsingRegex = re.compile(r'.*_(?P<date>\d{4}\d{2}\d{2})_(?P<time>\d{2}\d{2}\d{2}\d{3})')


## Format 7-29-2019:
videoFileNameMKVParsingRegex = re.compile(r'(?P<date>\d{4}\d{2}\d{2})_(?P<time>\d{2}\d{2}\d{2})(?P<time_msec>\d{3})?')
# Allow the last block (milliseconds) to be absent
# Examples: '20190722_140654', '20190723_155204'

## Format 11-7-2019: Supports detection of labeled videos
videoFileNameNew1ParsingRegex = re.compile(r'BehavioralBox_B(?P<bb_id>\d{2})_T(?P<date>\d{4}\d{2}\d{2})-(?P<time>\d{2}\d{2}\d{2})(?P<time_msec>\d{4})?(?P<deeplabcut_info>DLC_.+_labeled)?')
# Examples: 'BehavioralBox_B01_T20191002-0357260692.mp4', 'BehavioralBox_B00_T20190823-2150390329.mp4', 'BehavioralBox_B01_T20190919-1116320827DLC_resnet50_v3_oct29Oct29shuffle1_1030000_labeled.mp4'


## Format 12-17-2019: Supports detection of labeled videos
dataFileNameParsingRegex = re.compile(r'(?P<root_video_name>BehavioralBox_B(?P<bb_id>\d{2})_T(?P<date>\d{4}\d{2}\d{2})-(?P<time>\d{2}\d{2}\d{2})(?P<time_msec>\d{4})?)(?P<deeplabcut_info>DLC_.+)')
# Examples: 'BehavioralBox_B01_T20190918-0153290345DLC_resnet50_v3_oct29Oct29shuffle1_1030000.csv', 'BehavioralBox_B01_T20190918-0153290345DLC_resnet50_v3_oct29Oct29shuffle1_1030000includingmetadata.pickle', 'BehavioralBox_B01_T20190918-0153290345DLC_resnet50_v3_oct29Oct29shuffle1_1030000.h5'


# Both video_probe(...) and video_duration(...) are from https://stackoverflow.com/questions/3844430/how-to-get-the-duration-of-a-video-in-python
# they require the existance of "ffprobe.exe" at "C:/Common/bin/ffmpeg/bin/ffprobe.exe"
def video_probe(vid_file_path):
    ''' Give a json from ffprobe command line

    @vid_file_path : The absolute (full) path of the video file, string.
    '''
    if type(vid_file_path) != str:
        raise Exception('Give ffprobe a full file path of the video')
        return

    command = ["C:/Common/bin/ffmpeg/bin/ffprobe",
            "-loglevel",  "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            vid_file_path
            ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()
    return json.loads(out)

def video_duration(vid_file_path):
    ''' Video's duration in seconds, return a float number
    '''
    _json = video_probe(vid_file_path)

    if 'format' in _json:
        if 'duration' in _json['format']:
            return float(_json['format']['duration'])

    if 'streams' in _json:
        # commonly stream 0 is the video
        for s in _json['streams']:
            if 'duration' in s:
                return float(s['duration'])

    # if everything didn't happen,
    # we got here because no single 'return' in the above happen.
    raise Exception('I found no duration')
    #return None


class CachedFileSource(Enum):
    Unknown = 1
    OnlyFromDatabase = 2 # Indicates only loaded from database, not found in filesystem (or filesystem search isn't looking for this parent or it is but it isn't finished yet)
    OnlyFromFilesystem = 3 # Indicates the file doesn't exist in the database, and was only found in the filesystem
    NewestFromDatabase = 4 # Indcates the metadata hasn't be loaded from the filesystem or that the database version is newer for some reason
    NewestFromFilesystem = 5 # Indicates the loaded metadata is newer than the cached database version, and the database needs to be updated 
    Identical = 6 # 

# Any type of file found on the filesystem
class FoundFileResult(QObject):
    def __init__(self, path, parent_path, base_name, full_name, file_extension, extended_data=dict(), source=CachedFileSource.Unknown):
            super(FoundFileResult, self).__init__(None)
            self.path = path
            self.parent_path = parent_path
            self.base_name = base_name
            self.full_name = full_name
            self.file_extension = file_extension
            self.extended_data = extended_data
            self.source = source

    def get_full_name(self):
        return self.full_name

    def get_base_name(self):
        return self.base_name

    def get_source(self):
        return self.source

    def set_source(self, new_source):
        self.source = new_source

# A video file found on the filesystem
"""

"""


# The result of parsing a specific video
class VideoParsedResults(QObject):
    def __init__(self, duration, extended_data=dict()):
        super(VideoParsedResults, self).__init__(None)
        self.duration = duration

    def get_duration(self):
        secondsDuration = self.duration
        if secondsDuration is None:
            return None
        else:
            return timedelta(seconds=secondsDuration)

    def get_computed_end_date(self, start_date):
        secondsDuration = self.duration
        datetime_duration_end_object = start_date + timedelta(seconds=secondsDuration)
        return datetime_duration_end_object


class FoundVideoFileResult(FoundFileResult):

    def __init__(self, path, parent_path, base_name, full_name, file_extension, parsed_date, behavioral_box_id, is_deeplabcut_labeled_video, extended_data=dict(), source=CachedFileSource.Unknown):
            super(FoundVideoFileResult, self).__init__(path, parent_path, base_name, full_name, file_extension, extended_data, source)
            self.parsed_date = parsed_date
            self.behavioral_box_id = behavioral_box_id
            self.is_deeplabcut_labeled_video = is_deeplabcut_labeled_video
            self.video_parsed_results = None

    def get_parsed_start_date(self):
        return self.parsed_date

    def get_duration(self):
        if self.video_parsed_results:
            return self.video_parsed_results.get_duration()
        else:
            return None

    def get_computed_end_date(self):
        if self.video_parsed_results:
            return self.video_parsed_results.get_computed_end_date(self.parsed_date)
        else:
            return None

    def parse(self):
        # parse the video to find at least the duration
        duration = video_duration(self.path)
        # currProperties = get_media_properties(currPathString)
        self.video_parsed_results = VideoParsedResults(duration)
        pass


class FoundDeeplabcutOutputFileResult(FoundFileResult):

    def __init__(self, path, parent_path, base_name, full_name, file_extension, parsed_date, behavioral_box_id, base_video_file_name, deeplabcut_info_string, extended_data=dict(), source=CachedFileSource.Unknown):
            super(FoundDeeplabcutOutputFileResult, self).__init__(path, parent_path, base_name, full_name, file_extension, extended_data, source)
            self.parsed_date = parsed_date
            self.behavioral_box_id = behavioral_box_id
            self.base_video_file_name = base_video_file_name
            self.deeplabcut_info_string = deeplabcut_info_string

    def get_parsed_start_date(self):
        return self.parsed_date

    def get_base_video_file_name(self):
        return self.base_video_file_name
        
    def get_deeplabcut_info_string(self):
        return self.deeplabcut_info_string

    # def get_matching_video_base_name(self):
    #     self.get_base_name()


    # def get_duration(self):
    #     if self.video_parsed_results:
    #         return self.video_parsed_results.get_duration()
    #     else:
    #         return None

    # def get_computed_end_date(self):
    #     if self.video_parsed_results:
    #         return self.video_parsed_results.get_computed_end_date(self.parsed_date)
    #     else:
    #         return None

    # def parse(self):
    #     # parse the video to find at least the duration
    #     duration = video_duration(self.path)
    #     # currProperties = get_media_properties(currPathString)
    #     self.video_parsed_results = VideoParsedResults(duration)
    #     pass
    
# VideoParsedResults, FoundVideoFileResult
# VideoMetadataWorker, VideoMetadataWorkerSignals


## Finds the video files in the provided dir_path
def findVideoFiles(dir_path, shouldPrint=False):
    outputVideoFileInfoList = []
    entries = Path(dir_path)
    # Iterate through all directories in the path
    for entry in entries.iterdir():
        behavioral_box_id = None
        # Match .avi, .mp4, or .mkv files
        if fnmatch.fnmatch(entry.name, '*.avi') or fnmatch.fnmatch(entry.name, '*.mp4') or fnmatch.fnmatch(entry.name, '*.mkv'):
            # print(entry.name)
            info = entry.stat()
            #print(f'{entry.name}\t Last Modified: {convert_date(info.st_mtime)}')
            fileNameComponents = os.path.splitext(entry.name)
            fileBaseName = fileNameComponents[0]
            fileExtension = fileNameComponents[1]
            fileFullName = fileBaseName + fileExtension
            fileFullPath = entries.joinpath(entry.name).resolve(strict=True)
            fileParentPath = fileFullPath.parent

            # Start off unknown as to whether a given video a DLC labeled video
            is_deeplabcut_labeled_video = None

            #print('FileFullPath:', fileFullPath)
            #print('Filebasename: ', fileBaseName)
            # regex parse
            matches = videoFileNameParsingRegex.search(fileBaseName)
            if ((matches is not None)):
                tempParsableDateString = matches.group('date') + ' ' + matches.group('time')
                # 'yyyyMMdd''T''HHmmssSSS'
                datetime_object = datetime.strptime(tempParsableDateString, '%Y%m%d %H%M%S%f')
                datetime_object = datetime_object.replace(tzinfo=timezone.utc)
            else:
                matches = videoFileNameMKVParsingRegex.search(fileBaseName)
                if ((matches is not None)):
                    tempParsableDateString = matches.group('date') + ' ' + matches.group('time')
                    # 'yyyyMMdd''T''HHmmssSSS'
                    datetime_object = datetime.strptime(tempParsableDateString, '%Y%m%d %H%M%S%f')
                    datetime_object = datetime_object.replace(tzinfo=timezone.utc)
                else:
                    matches = videoFileNameNew1ParsingRegex.search(fileBaseName)
                    if ((matches is not None)):
                        tempParsableDateString = matches.group('date') + ' ' + matches.group('time')
                        if matches.group('time_msec'):
                            tempParsableDateString = tempParsableDateString + matches.group('time_msec') # Get millisecond component if it exists

                        # 'yyyyMMdd''T''HHmmssSSS'
                        datetime_object = datetime.strptime(tempParsableDateString, '%Y%m%d %H%M%S%f')
                        datetime_object = datetime_object.replace(tzinfo=timezone.utc)

                        behavioral_box_id = int(matches.group('bb_id'))

                        if matches.group('deeplabcut_info'):
                            is_deeplabcut_labeled_video = True
                        else:
                            is_deeplabcut_labeled_video = False

                    else:
                        continue



            # If the full file path exists (which it should, since we just found it)
            if fileFullPath.exists():
                currPathString = str(fileFullPath)

                # Try to get the extended media properties, like the duration
                # currProperties = get_media_properties(currPathString)
                # extendedProperties = get_video_extended_metadata(currPathString)
                currProperties = None
                extendedProperties = None

                if extendedProperties is None:
                    # continue
                    extendedProperties = dict()
                    extendedProperties['behavioral_box_id'] = behavioral_box_id
                else:
                   extendedProperties['behavioral_box_id'] = behavioral_box_id

                # Check if the returned properties are empty
                if currProperties:
                    # Returns the duration in seconds
                    secondsDuration = currProperties['duration']
                    datetime_duration_end_object = datetime_object + timedelta(seconds=secondsDuration)
                else:
                    currProperties = None
                    datetime_duration_end_object = None

                if shouldPrint:
                    print("Found: ", currPathString, "  parsed_date", datetime_object, " - Properties: ", currProperties, extendedProperties)

                # currOutputDict = {'base_name': fileBaseName, 'file_fullname': fileFullName, 'file_extension': fileExtension, 'parent_path': fileParentPath, 'path': currPathString, 'parsed_date': datetime_object, 'computed_end_date': datetime_duration_end_object, 'is_deeplabcut_labeled_video': is_deeplabcut_labeled_video, 'properties': currProperties, 'extended_properties': extendedProperties}
                # outputVideoFileInfoList.append(currOutputDict)

                currOutputObj = FoundVideoFileResult(currPathString, fileParentPath, fileBaseName, fileFullName, fileExtension, datetime_object, behavioral_box_id, is_deeplabcut_labeled_video)
                currOutputObj.parse()
                outputVideoFileInfoList.append(currOutputObj)

                
            else:
                print("Path doesn't exist!")

    return outputVideoFileInfoList


## Finds the DeeplabCut (DLC) produced .csv, .h5, .pickle files in the provided dir_path
def findDeeplabCutProducedOutputFiles(dir_path, shouldPrint=False):
    outputFileInfoList = []
    entries = Path(dir_path)
    # Iterate through all directories in the path
    for entry in entries.iterdir():
        behavioral_box_id = None
        # Match .avi, .mp4, or .mkv files
        if fnmatch.fnmatch(entry.name, '*.csv') or fnmatch.fnmatch(entry.name, '*.h5') or fnmatch.fnmatch(entry.name, '*includingmetadata.pickle'):
            # print(entry.name)
            info = entry.stat()
            #print(f'{entry.name}\t Last Modified: {convert_date(info.st_mtime)}')
            fileNameComponents = os.path.splitext(entry.name)
            fileBaseName = fileNameComponents[0]
            fileExtension = fileNameComponents[1]
            fileFullName = fileBaseName + fileExtension
            fileFullPath = entries.joinpath(entry.name).resolve(strict=True)
            fileParentPath = fileFullPath.parent

            # Start off unknown as to whether a given video a DLC labeled video
            deeplabcut_info_string = None
            original_video_basename_string = None
            #print('FileFullPath:', fileFullPath)
            #print('Filebasename: ', fileBaseName)
            # regex parse
            matches = dataFileNameParsingRegex.search(fileBaseName)
            if ((matches is not None)):
                tempParsableDateString = matches.group('date') + ' ' + matches.group('time')
                if matches.group('time_msec'):
                    tempParsableDateString = tempParsableDateString + matches.group('time_msec') # Get millisecond component if it exists

                # 'yyyyMMdd''T''HHmmssSSS'
                datetime_object = datetime.strptime(tempParsableDateString, '%Y%m%d %H%M%S%f')
                datetime_object = datetime_object.replace(tzinfo=timezone.utc)

                behavioral_box_id = int(matches.group('bb_id'))

                if matches.group('deeplabcut_info'):
                    deeplabcut_info_string = str(matches.group('deeplabcut_info'))
                else:
                    print("Couldn't get DLC info string for file {0}. Skipping.".format(str(fileFullName)))
                    continue

                if matches.group('root_video_name'):
                    original_video_basename_string = str(matches.group('root_video_name'))
                else:
                    print("Couldn't get original video basename string for file {0}. Skipping.".format(str(fileFullName)))
                    continue

            else:
                continue



            # If the full file path exists (which it should, since we just found it)
            if fileFullPath.exists():
                currPathString = str(fileFullPath)

                # Try to get the extended media properties, like the duration
                # currProperties = get_media_properties(currPathString)
                # extendedProperties = get_video_extended_metadata(currPathString)
                currProperties = None
                extendedProperties = None

                if extendedProperties is None:
                    # continue
                    extendedProperties = dict()
                    extendedProperties['behavioral_box_id'] = behavioral_box_id
                else:
                   extendedProperties['behavioral_box_id'] = behavioral_box_id

                # Check if the returned properties are empty

                extendedProperties['deeplabcut_info_string'] = deeplabcut_info_string
                extendedProperties['original_video_basename_string'] = original_video_basename_string

                if shouldPrint:
                    print("Found: ", currPathString, "  parsed_date", datetime_object, " - Properties: ", currProperties, extendedProperties)

                # currOutputDict = {'base_name': fileBaseName, 'file_fullname': fileFullName, 'file_extension': fileExtension, 'parent_path': fileParentPath, 'path': currPathString, 'parsed_date': datetime_object, 'computed_end_date': datetime_duration_end_object, 'is_deeplabcut_labeled_video': is_deeplabcut_labeled_video, 'properties': currProperties, 'extended_properties': extendedProperties}
                # outputVideoFileInfoList.append(currOutputDict)

                # currOutputObj = FoundVideoFileResult(currPathString, fileParentPath, fileBaseName, fileFullName, fileExtension, datetime_object, behavioral_box_id, is_deeplabcut_labeled_video)
                # currOutputObj.parse()

                currOutputObj = FoundDeeplabcutOutputFileResult(currPathString, fileParentPath, fileBaseName, fileFullName, fileExtension, datetime_object, behavioral_box_id, original_video_basename_string, deeplabcut_info_string)
                # currOutputObj.parse()
                outputFileInfoList.append(currOutputObj)

                
            else:
                print("Path doesn't exist!")

    return outputFileInfoList
