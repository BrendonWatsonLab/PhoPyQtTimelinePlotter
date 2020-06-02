# -*- mode: python -*-

## Used Info:

## Problem:
# __main__.PyInstallerImportError: Failed to load dynlib/dll 'libvlc.dll'. Most probably this dynlib/dll was not found when the application was frozen.
## Solution: 
# https://stackoverflow.com/questions/48336981/how-can-i-convince-pyinstaller-via-my-spec-file-to-include-libvlc-dll-in-the-e
# https://stackoverflow.com/questions/57641737/pyinstaller-cannot-find-libvlc-dll
# https://github.com/pyinstaller/pyinstaller/issues/3448


## Problem:
# qt.qpa.plugin: Could not find the Qt platform plugin "windows" in ""
# This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.
## Solution: 
# https://stackoverflow.com/questions/56560515/qt-qpa-plugin-could-not-find-the-qt-platform-plugin-windows-in
# https://stackoverflow.com/questions/47468705/pyinstaller-could-not-find-or-load-the-qt-platform-plugin-windows


## Problem:
# ImportError: Could not resolve module sqlalchemy.ext.baked
## Solution:
    # http://pyinstaller.47505.x6.nabble.com/ImportError-Could-not-resolve-module-sqlalchemy-ext-baked-td2358.html


## Problem:
# FileNotFoundError: [Errno 2] No such file or directory: 'GUI/MainWindow/MainWindow.ui'
# [2008] Failed to execute script main
# Copied C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\platforms to ./platforms and C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\styles to ./styles
block_cipher = None

added_binaries = [
         ( 'C:\Program Files\VideoLAN\VLC\*.dll', '.' ),
         ( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\platforms', 'platforms' ),
         ( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\styles', 'styles' )
        #  ( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\platforms', '.' ),
        #  ( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\styles', '.' )
         ]

#( 'C:\Program Files\VideoLAN\VLC\libvlc.dll', '.' ),
#( 'C:\Program Files\VideoLAN\VLC\libvlccore.dll', '.' ),
#( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\platforms\qwindows.dll', '.' ),
#( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\styles\qwindowsvistastyle.dll', '.' )

# "C:\\Users\\halechr\\repo\\PhoPyQtTimelinePlotter\\data\\fonts\\HelveticaNeue.ttf"
# 
added_files = [
         ( 'EXTERNAL/README.md', '.' ),
         ( 'C:\Program Files\VideoLAN\VLC\plugins', 'plugins' ),
         ( 'GUI/application.qss', 'GUI' ),
         ( 'GUI/HelpWindow/HelpWindow.ui', 'GUI/HelpWindow' ),
         ( 'GUI/MainObjectListsWindow/MainObjectListsWindow.ui', 'GUI/MainObjectListsWindow' ),
         ( 'GUI/MainWindow/MainWindow.ui', 'GUI/MainWindow' ),
         ( 'GUI/SetupWindow/SetupWindow.ui', 'GUI/SetupWindow' ),
         ( 'GUI/UI/DialogComponents/BoxExperCohortAnimalIDs_DialogComponents.ui', 'GUI/UI/DialogComponents' ),
         ( 'GUI/UI/DialogComponents/StartEndDate_DialogComponents.ui', 'GUI/UI/DialogComponents' ),
         ( 'GUI/UI/DialogComponents/TitleSubtitleBody_DialogComponents.ui', 'GUI/UI/DialogComponents' ),
         ( 'GUI/UI/DialogComponents/TypeSubtype_DialogComponents.ui', 'GUI/UI/DialogComponents' ),
         ( 'GUI/UI/DialogComponents/ImportContext_DialogComponents.ui', 'GUI/UI/DialogComponents' ),
         ( 'GUI/UI/DialogComponents/ListLockableEditButtons_DialogComponents.ui', 'GUI/UI/DialogComponents' ),
         ( 'GUI/UI/DialogComponents/LockableList.ui', 'GUI/UI/DialogComponents' ),
         ( 'GUI/UI/ExperimentalConfigEditDialogs/AnimalEditDialog.ui', 'GUI/UI/ExperimentalConfigEditDialogs' ),
         ( 'GUI/UI/ImportCSVWidget/ImportCSVWidget.ui', 'GUI/UI/ImportCSVWidget' ),
         ( 'GUI/UI/PartitionEditDialog/PartitionEditDialog.ui', 'GUI/UI/PartitionEditDialog' ),
         ( 'GUI/UI/ReferenceMarkViewer/ReferenceMarkViewer.ui', 'GUI/UI/ReferenceMarkViewer' ),
         ( 'GUI/UI/ReferenceMarkViewer/DockWidget_ReferenceMarkViewer.ui', 'GUI/UI/ReferenceMarkViewer' ),
         ( 'GUI/UI/TextAnnotations/TextAnnotations.ui', 'GUI/UI/TextAnnotations' ),
         ( 'GUI/UI/TimelineFloatingHeaderWidget/TimelineFloatingHeaderWidget.ui', 'GUI/UI/TimelineFloatingHeaderWidget' ),
         ( 'GUI/UI/TimelineHeaderWidget/TimelineHeaderWidget_ContentsCollapsed.ui', 'GUI/UI/TimelineHeaderWidget' ),
         ( 'GUI/UI/TimelineHeaderWidget/TimelineHeaderWidget_ContentsExpanded.ui', 'GUI/UI/TimelineHeaderWidget' ),
         ( 'GUI/UI/TimelineHeaderWidget/TimelineHeaderWidget.ui', 'GUI/UI/TimelineHeaderWidget' ),
         ( 'GUI/UI/VideoEditDialog/VideoEditDialog.ui', 'GUI/UI/VideoEditDialog' ),
         ( 'GUI/UI/VideoTrackFilterEditWidget/VideoTrackFilterEditWidget.ui', 'GUI/UI/VideoTrackFilterEditWidget' ),
         ( 'GUI/UI/VideoTrackFilterEditWidget/VideoTrackFilterEditDialog.ui', 'GUI/UI/VideoTrackFilterEditWidget' ),
         ( 'GUI/Windows/ImportCSVWindow/ImportCSVWindow.ui', 'GUI/Windows/ImportCSVWindow' ),
         ( 'GUI/Windows/VideoPlayer/MainVideoPlayerWindow.ui', 'GUI/Windows/VideoPlayer' ),
         ( 'GUI/Windows/VideoPlayer/VideoPlayerWidget.ui', 'GUI/Windows/VideoPlayer' ),
         ( 'GUI/Windows/VideoPlayer/VideoPlayerWindow_TimestampSidebarWidget.ui', 'GUI/Windows/VideoPlayer' )
         ]

         

#         ( 'EXTERNAL/Dependencies/ffmpeg', 'EXTERNAL/Dependencies/ffmpeg'),
#( 'EXTERNAL\Databases\*.db', 'EXTERNAL\Databases\' )
# 'EXTERNAL\Dependencies\ffmpeg'

added_hiddenimports=['sqlalchemy.ext.baked']


a = Analysis(['main.py'],
             pathex=['C:\\Users\\halechr\\repo\\PhoPyQtTimelinePlotter'],
             binaries=added_binaries,
             datas=added_files,
             hiddenimports=added_hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=True,
             win_private_assemblies=True,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='main')
