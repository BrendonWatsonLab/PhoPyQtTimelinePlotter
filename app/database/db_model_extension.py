from pathlib import Path
from datetime import datetime

## This file exists to extend the classes auto-generated in db_model.py
from app.database.db_model import VideoFile

class ExVideoFile(VideoFile):

    def factory(aPhoDurationVideoEvent):
        # outObj.file_fullname = aPhoDurationVideoEvent.extended_data['fullpath']
        aFullPath = aPhoDurationVideoEvent.extended_data['fullpath']
        aFullParentPath = str(aPhoDurationVideoEvent.extended_data['parent_path'])  # The parent path
        aFullName = aPhoDurationVideoEvent.name  # The full name including extension
        aBaseName = aPhoDurationVideoEvent.extended_data['base_name']  # Excluding the period and extension
        anExtension = aPhoDurationVideoEvent.extended_data['file_extension'][1:]  # the file extension excluding the period
        if (not aPhoDurationVideoEvent.extended_data['behavioral_box_id'] is None):
            aBBID = aPhoDurationVideoEvent.extended_data['behavioral_box_id'] + 1  # Add one to get a valid index
        else:
            aBBID = 1

        if (not aPhoDurationVideoEvent.extended_data['is_deeplabcut_labeled_video'] is None):
            is_deeplabcut_labeled_video = aPhoDurationVideoEvent.extended_data['is_deeplabcut_labeled_video']
            is_original_video = (not is_deeplabcut_labeled_video)
        else:
            is_deeplabcut_labeled_video = None
            is_original_video = None  # We know nothing about whether it is an original video

        anExperimentID = 1
        aCohortID = 1
        anAnimalID = 3
        notes = ''
        startTime = int(aPhoDurationVideoEvent.startTime.timestamp() * 1000.0)
        endTime = int(aPhoDurationVideoEvent.endTime.timestamp() * 1000.0)
        duration = int(aPhoDurationVideoEvent.computeDuration().total_seconds() * 1000.0)

        return ExVideoFile(None, aFullName, aBaseName, anExtension, aFullParentPath, startTime, endTime, duration, aBBID, anExperimentID, aCohortID, anAnimalID, is_original_video, notes)

    factory = staticmethod(factory)

    def get_start_date(self):
        return datetime.fromtimestamp(float(self.start_date) / 1000.0)

    def get_end_date(self):
        return datetime.fromtimestamp(float(self.end_date) / 1000.0)

    def get_duration(self):
        return float(self.duration) / 1000.0

    def get_extension(self):
        return ('.' + self.file_extension)  # Add the period back on

    def get_full_path(self):
        entries = Path(self.file_video_folder)
        return entries.joinpath(self.file_fullname).resolve(strict=True)

    def get_is_deeplabcut_labeled_video(self):
        # Allow being undecided as to whether a video is an original or not
        if (self.is_original_video is None):
            return None
        else:
            return (not self.is_original_video)

    def get_currProperties(self):
        return {'duration': self.get_duration()}

    def get_extendedProperties(self):
        return {'behavioral_box_id': self.behavioral_box_id}

    def get_output_dict(self):
        return {'base_name': self.file_basename, 'file_fullname': self.file_fullname, 'file_extension': self.get_extension(), 'parent_path': self.file_video_folder, 'path': self.get_full_path(), 'parsed_date': self.get_start_date(), 'computed_end_date': self.get_end_date(), 'is_deeplabcut_labeled_video': self.get_is_deeplabcut_labeled_video(), 'properties': self.get_currProperties(), 'extended_properties': self.get_extendedProperties()}