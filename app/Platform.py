# Platform.py
import pathlib
from enum import Enum

from PyQt5.QtCore import Qt, QObject, QDir

# A variable the holds the configuration for the current operating system
class PlatformOperatingSystem(Enum):
    Windows = 1
    Mac = 2
    Linux = 3
    Unknown = 4

    def get_project_directory(self):
        if (self is PlatformOperatingSystem.Windows):
            return pathlib.Path("C:/Users/halechr/repo/PhoPyQtTimelinePlotter/")
        elif (self is PlatformOperatingSystem.Mac):
            return pathlib.Path("/Users/pho/repo/PhoPyQtTimelinePlotter/")
        elif (self is PlatformOperatingSystem.Linux):
            print("ERROR: Linux not implemented, set the path in main.py")
            raise NotImplementedError
            # return pathlib.Path("/Users/pho/repo/PhoPyQtTimelinePlotter/")
        else:
            print("ERROR: Unknown Type")
            raise NotImplementedError
            return None


# PlatformConfiguration: contains parameters specific to the current running instance of the program, like the project path, the OS it's running on (Mac/Win/Linux), etc.
class PlatformConfiguration(QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.operatingSystem = PlatformOperatingSystem.Unknown
        self.project_directory = None
        self.determineOS()


    def determineOS(self):
        project_directory_windows = PlatformOperatingSystem.Windows.get_project_directory()
        project_directory_mac = PlatformOperatingSystem.Mac.get_project_directory()

        if (project_directory_windows.exists()):
            # platform is Windows
            self.operatingSystem = PlatformOperatingSystem.Windows
            self.project_directory = project_directory_windows
        
        elif (project_directory_mac.exists()):
            # platform is Mac
            self.operatingSystem = PlatformOperatingSystem.Mac
            self.project_directory = project_directory_mac

        else:
            print("ERROR: none of the expected project directories exist!")
            new_user_dir = None
            # Todo: allow user to specify a dir
            if new_user_dir is not None:
                new_user_dir = new_user_dir.resolve()

            self.operatingSystem = PlatformOperatingSystem.Unknown
            self.project_directory = new_user_dir

    def get_ffmpeg_directory(self):
        return self.get_project_directory().joinpath("EXTERNAL", "Dependencies", "ffmpeg", "bin")

    def get_ffprobe_executable_path_string(self):
        return str(self.get_ffmpeg_directory().joinpath("ffprobe"))

    def get_project_directory(self):
        return self.project_directory

