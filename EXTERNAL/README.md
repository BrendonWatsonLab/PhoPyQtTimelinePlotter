
## Hierarchy:

## app/filesystem/FilesystemRecordBase.py
# FilesystemRecordBase: an attempt to make a "record" like object for events loaded from filesystem files analagous to the records loaded from the database
# FilesystemLabjackEvent_Record: for labjack events loaded from a labjack data file

## app/filesystem/LabjackEventsLoader.py
# LabjackEventType
# LabjackEventsLoader
#   from app.filesystem.FilesystemRecordBase import FilesystemRecordBase, FilesystemLabjackEvent_Record

## app/filesystem/LabjackFilesystemLoadingMixin.py
# LabjackFilesystemLoader: this object tries to find Labjack-exported data files in the filesystem and make them accessible in memory
    # load_labjack_data_files(...): this is the main function that searches the listed paths for labjack data files, and then loads them into memory.
# LabjackEventFile: a single imported data file containing one or more labjack events.
#   from app.filesystem.LabjackEventsLoader import LabjackEventsLoader, PhoServerFormatArgs
#   from app.filesystem.FilesystemRecordBase import FilesystemRecordBase, FilesystemLabjackEvent_Record





## GUI/TimelineTrackWidgets/TimelineTrackDrawingWidget_DataFile.py


## GUI/Model/TrackConfigs/DataFileTrackConfig.py

