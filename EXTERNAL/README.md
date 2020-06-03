
## Requirements:
VLC 3.0.8 Vetinari

(Py3PyQt5)

# Creating an Environment:
conda env export > EXTERNAL\Requirements\06-01-2020\environment.yml
conda env export --no-builds > EXTERNAL\Requirements\06-01-2020\environment_no_builds.yml

conda env export --from-history > EXTERNAL\Requirements\06-03-2020\environment.yml


## Spec-File:
conda list --explicit > EXTERNAL\Requirements\06-01-2020\spec-file.txt
# Installing from Spec-file:
conda create --name Py3PyQt5New --file EXTERNAL\Requirements\06-01-2020\spec-file.txt


#  Making a clone:
conda create --name Py3PyQt5_Testing --clone Py3PyQt5


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

