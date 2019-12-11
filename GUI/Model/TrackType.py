import sys
from enum import Enum

## IMPORT:
# from GUI.Model.TrackType import TrackType, TrackStorageArray

class TrackStorageArray(Enum):
    Unknown = 1
    Video = 2
    Event = 3


class TrackType(Enum):
    Unknown = 1
    Video = 2
    Annotation = 3
    Partition = 4

    def get_short_str(self):
        if self == TrackType.Unknown:
            return '?'
        elif self == TrackType.Video:
            return 'V'
        elif self == TrackType.Annotation:
            return 'A'
        elif self == TrackType.Partition:
            return 'P'
        else:
            return '!'

    def get_medium_str(self):
        if self == TrackType.Unknown:
            return '???'
        elif self == TrackType.Video:
            return 'Vid'
        elif self == TrackType.Annotation:
            return 'Note'
        elif self == TrackType.Partition:
            return 'Part'
        else:
            return 'ERR'

    def get_long_str(self):
        if self == TrackType.Unknown:
            return 'Unknown'
        elif self == TrackType.Video:
            return 'Video'
        elif self == TrackType.Annotation:
            return 'Annotation'
        elif self == TrackType.Partition:
            return 'Partition'
        else:
            return 'ERROR'

    def get_storage_array_type(self):
        if self == TrackType.Unknown:
            return TrackStorageArray.Unknown
        elif self == TrackType.Video:
            return TrackStorageArray.Video
        elif self == TrackType.Annotation:
            return TrackStorageArray.Event
        elif self == TrackType.Partition:
            return TrackStorageArray.Event
        else:
            return TrackStorageArray.Unknown

    def __str__(self):
        return self.get_long_str()



# TrackConfigMixin: Used to get the config 
class TrackConfigMixin(object):
    # Track config functions
    def get_track_config(self):
        return self.trackConfig

    def get_track_filter(self):
        return self.get_track_config().get_filter()

    def get_track_type(self):
        return self.get_track_filter().get_track_type()