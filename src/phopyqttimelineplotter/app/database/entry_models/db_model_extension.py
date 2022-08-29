from pathlib import Path
from datetime import datetime

## This file exists to extend the classes auto-generated in db_model.py
from phopyqttimelineplotter.app.database.entry_models.db_model import VideoFile

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
