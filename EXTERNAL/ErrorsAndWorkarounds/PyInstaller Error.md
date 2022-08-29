
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