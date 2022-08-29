# Requires ffprobe binary installed in ./EXTERNAL/Dependencies/ffmpeg/bin/ffprobe. Obtainable from https://ffmpeg.zeranoe.com/builds/. Tested with 4.2.1


In general each track widget has the following setup:


## Creation:
        self.partitionsTrackWidget = TimelineTrackDrawingWidget_Partition(-1, None, [], self.totalStartTime, self.totalEndTime)

## Layout:
        self.extendedTracksContainerVboxLayout.addWidget(self.partitionsTrackWidget)
        self.partitionsTrackWidget.setMinimumSize(500,50)
        self.partitionsTrackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)




GENERAL TODO:
 - "Comments" Track: multiline comments previewed in timeline, with popover text display and editor.
    - Perhaps preview of text of hovered comments in another pane or the status bar.
    - Perhaps allowing user color coding or short text to be displayed on the comment itself.
    - Perhaps support for instantaneous, duration, or file comments.

- "Video" Track: displays videos along a full timeline.
    - Perhaps multiple video tracks allowed, one for original source videos and another for DeepLabCut processed videos for example.

- Need to be able to adjust "zoom".


Generate .py files from .ui files: (NOT NEEDED)
/Users/pho/opt/anaconda3/envs/Py3Qt5/bin/pyuic5 -d /Users/pho/repo/PhoPyQtTimelinePlotter/GUI/SetupWindow/SetupWindow.ui -o /Users/pho/repo/PhoPyQtTimelinePlotter/GUI/SetupWindow/SetupWindow-AutoGen.py

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


## PyInstaller Error:
(Py3PyQt5) C:\Users\halechr\repo\PhoPyQtTimelinePlotter\dist\main>main.exe
C:\ProgramData\Anaconda3\envs\Py3PyQt5\lib\site-packages\PyInstaller\loader\pyimod03_importers.py:627: MatplotlibDeprecationWarning:
The MATPLOTLIBDATA environment variable was deprecated in Matplotlib 3.1 and will be removed in 3.3.
  exec(bytecode, module.__dict__)
Traceback (most recent call last):
  File "site-packages\PyInstaller\loader\pyiboot01_bootstrap.py", line 149, in __init__
  File "ctypes\__init__.py", line 348, in __init__
OSError: [WinError 126] The specified module could not be found

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "PhoPyQtTimelinePlotter\main.py", line 21, in <module>
  File "<frozen importlib._bootstrap>", line 971, in _find_and_load
  File "<frozen importlib._bootstrap>", line 955, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 665, in _load_unlocked
  File "C:\ProgramData\Anaconda3\envs\Py3PyQt5\lib\site-packages\PyInstaller\loader\pyimod03_importers.py", line 627, in exec_module
    exec(bytecode, module.__dict__)
  File "PhoPyQtTimelinePlotter\GUI\MainWindow\TimelineDrawingWindow.py", line 36, in <module>
  File "<frozen importlib._bootstrap>", line 971, in _find_and_load
  File "<frozen importlib._bootstrap>", line 955, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 665, in _load_unlocked
  File "C:\ProgramData\Anaconda3\envs\Py3PyQt5\lib\site-packages\PyInstaller\loader\pyimod03_importers.py", line 627, in exec_module
    exec(bytecode, module.__dict__)
  File "PhoPyQtTimelinePlotter\GUI\Windows\VideoPlayer\__init__.py", line 6, in <module>
  File "<frozen importlib._bootstrap>", line 971, in _find_and_load
  File "<frozen importlib._bootstrap>", line 955, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 665, in _load_unlocked
  File "C:\ProgramData\Anaconda3\envs\Py3PyQt5\lib\site-packages\PyInstaller\loader\pyimod03_importers.py", line 627, in exec_module
    exec(bytecode, module.__dict__)
  File "PhoPyQtTimelinePlotter\GUI\Windows\VideoPlayer\MainVideoPlayerWindow.py", line 14, in <module>
  File "<frozen importlib._bootstrap>", line 971, in _find_and_load
  File "<frozen importlib._bootstrap>", line 955, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 665, in _load_unlocked
  File "C:\ProgramData\Anaconda3\envs\Py3PyQt5\lib\site-packages\PyInstaller\loader\pyimod03_importers.py", line 627, in exec_module
    exec(bytecode, module.__dict__)
  File "PhoPyQtTimelinePlotter\lib\vlc.py", line 207, in <module>
  File "PhoPyQtTimelinePlotter\lib\vlc.py", line 163, in find_lib
  File "site-packages\PyInstaller\loader\pyiboot01_bootstrap.py", line 151, in __init__
__main__.PyInstallerImportError: Failed to load dynlib/dll 'libvlc.dll'. Most probably this dynlib/dll was not found when the application was frozen.
[8988] Failed to execute script main