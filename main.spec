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

block_cipher = None

added_binaries = [
         ( 'C:\Program Files\VideoLAN\VLC\*.dll', '.' ),
         ( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\platforms', '.' ),
         ( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\styles', '.' )
         ]

#( 'C:\Program Files\VideoLAN\VLC\libvlc.dll', '.' ),
#( 'C:\Program Files\VideoLAN\VLC\libvlccore.dll', '.' ),
#( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\platforms\qwindows.dll', '.' ),
#( 'C:\ProgramData\Anaconda3\envs\Py3PyQt5\Library\plugins\styles\qwindowsvistastyle.dll', '.' )


added_files = [
         ( 'EXTERNAL/README.md', '.' ),
         ( 'C:\Program Files\VideoLAN\VLC\plugins', 'plugins' )
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
