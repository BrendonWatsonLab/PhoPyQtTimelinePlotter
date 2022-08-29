# Requirements:

- Requires ffprobe binary installed in ./EXTERNAL/Dependencies/ffmpeg/bin/ffprobe. Obtainable from https://ffmpeg.zeranoe.com/builds/. Tested with 4.2.1


# Generating Documentation
`mamba install pdoc -c conda-forge`

pdoc . --output-directory EXTERNAL/DOCS/GENERATED


# 2022-08-29 General Data Import Test (.h5 and .npz):
r'C:\Users\pho\repos\PhoPy3DPositionAnalysis2021\data\pipeline_cache_store.h5'
r'C:/Users/pho/repos/PhoPy3DPositionAnalysis2021/data/completed_pipeline.npz'

TimelineDrawingWindow.on_user_general_h5_data_load()
User canceled the import!
TimelineDrawingWindow.on_user_general_npz_data_load()
Importing data file at path C:/Users/pho/repos/PhoPy3DPositionAnalysis2021/data/completed_pipeline.npz...
Traceback (most recent call last):
  File "c:\Users\pho\repos\PhoPyQtTimelinePlotter\GUI\MainWindow\TimelineDrawingWindow.py", line 2787, in on_user_general_npz_data_load
    self.get_general_npz_data_files_loader().add_actigraphy_file_path(importFilePath)
  File "c:\Users\pho\repos\PhoPyQtTimelinePlotter\GUI\MainWindow\TimelineDrawingWindow.py", line 2792, in get_general_npz_data_files_loader
    return self.actigraphyDataFilesystemLoader
AttributeError: 'TimelineDrawingWindow' object has no attribute 'actigraphyDataFilesystemLoader'


# Track Widget Setup

In general each track widget has the following setup:

## Creation:
        self.partitionsTrackWidget = TimelineTrackDrawingWidget_Partition(-1, None, [], self.totalStartTime, self.totalEndTime)

## Layout:
        self.extendedTracksContainerVboxLayout.addWidget(self.partitionsTrackWidget)
        self.partitionsTrackWidget.setMinimumSize(500,50)
        self.partitionsTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)



# GENERAL TODO:
 - "Comments" Track: multiline comments previewed in timeline, with popover text display and editor.
    - Perhaps preview of text of hovered comments in another pane or the status bar.
    - Perhaps allowing user color coding or short text to be displayed on the comment itself.
    - Perhaps support for instantaneous, duration, or file comments.

- "Video" Track: displays videos along a full timeline.
    - Perhaps multiple video tracks allowed, one for original source videos and another for DeepLabCut processed videos for example.

- Need to be able to adjust "zoom".




cd "C:\Program Files\VideoLAN\VLC\"
vlc-cache-gen.exe "C:\Program Files\VideoLAN\VLC\plugins\"
Running C:\Program Files\VideoLAN\VLC>vlc-cache-gen.exe "C:\Program Files\VideoLAN\VLC\plugins\"
fixes the VLC cache errors that appear in the terminal that result in slow video opening.
        See https://dev.getsol.us/T5893 for more info
        https://www.reddit.com/r/VLC/comments/9y63by/fix_slow_starting_vlc_30x_on_windows_10_by/


Upon modifying the .qrc resource (containing icons and stuff), it will need to be re-build using "rcc -binary myresource.qrc -o myresource.rcc". This .rcc file is loaded in the main.py and without it icons would be broken.
See https://doc.qt.io/qt-5/resources.html for more info.
        For example:
                rcc -binary "C:\Users\halechr\repo\PhoPyQtTimelinePlotter\data\PhoPyQtTimelinePlotterResourceFile.qrc" -o "C:\Users\halechr\repo\PhoPyQtTimelinePlotter\data\PhoPyQtTimelinePlotterResourceFile.rcc"


## FFMPEG Experimentation:
        "//10.17.158.49/ServerInternal-01/Transcoded Videos/BB00/BehavioralBox_B00_T20190812-1348550224.mp4"
        "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/data/output/temp.jpg"
        ffmpeg -i "//10.17.158.49/ServerInternal-01/Transcoded Videos/BB00/BehavioralBox_B00_T20190812-1348550224.mp4" -ss 00:00:00.000 -vframes 1 "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/data/output/temp.jpg"
        -an
        ffmpeg -i "//10.17.158.49/ServerInternal-01/Transcoded Videos/BB00/BehavioralBox_B00_T20190812-1348550224.mp4" -ss 02:00:00.000 -vframes 1 "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/data/output/temp-2.jpg"

