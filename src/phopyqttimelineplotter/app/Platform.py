# Platform.py
import pathlib
from enum import Enum
import configparser

from PyQt5.QtCore import Qt, QObject, QDir

# Manages loading/saving values to a .ini configuration file
class ConfigManager(object):

    def __init__(self, config_path='data/config.ini', parent=None):
        # super().__init__(parent=parent)
        super().__init__()
        self.config_file_path = config_path
        self.config = configparser.ConfigParser()
        self.read_from_file()

    def get_config(self):
        return self.config
        
    def create_sample_config(self):
        self.config['DEFAULT'] = {'ProjectDirectory': "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/",
            'FFMPEGPath': "EXTERNAL/Dependencies/ffmpeg/bin",
            'Compression': 'yes'}


            # config['DEFAULT']['ProjectDirectory']
            # config['DEFAULT']['FFMPEGPath']
        
    def read_from_file(self, override_path = None):
        if override_path is not None:
            self.config_file_path = override_path

        self.config.read(self.config_file_path)   

    def write_to_file(self, override_path = None):
        if override_path is not None:
            self.config_file_path = override_path

        with open(self.config_file_path, 'w') as configfile:
            self.config.write(configfile)

# A variable the holds the configuration for the current operating system
class PlatformOperatingSystem(Enum):
    Windows = 1
    Mac = 2
    Linux = 3
    Unknown = 4

    def get_project_directory(self):
        currConfigManagerConfig = ConfigManager().get_config()
        # currConfigFileSpecified_Project_dir = currConfigManagerConfig['DEFAULT']['ProjectDirectory']
        
        # TODO: I think when the config file contains an empty string, the potential_path returns pathlib.Path('.') which might be exactly what we want.
        # As a result, I don't think this is ever ran.
        if (self is PlatformOperatingSystem.Windows):
            # return pathlib.Path("C:/Users/halechr/repo/PhoPyQtTimelinePlotter/")
            fallback_path = "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/"
        elif (self is PlatformOperatingSystem.Mac):
            # return pathlib.Path("/Users/pho/repo/PhoPyQtTimelinePlotter/")
            fallback_path = "/Users/pho/repo/PhoPyQtTimelinePlotter/"
        elif (self is PlatformOperatingSystem.Linux):
            print("ERROR: Linux not implemented, set the path in main.py")
            raise NotImplementedError
            # return pathlib.Path("/Users/pho/repo/PhoPyQtTimelinePlotter/")
        else:
            print("ERROR: Unknown Type")
            raise NotImplementedError
            return None

        currConfigFileSpecified_Project_dir = currConfigManagerConfig.get('DEFAULT', 'ProjectDirectory', fallback=fallback_path)
        # print('found proj dir: {} from config'.format(currConfigFileSpecified_Project_dir))
        if currConfigFileSpecified_Project_dir is not None:
            potential_path = pathlib.Path(currConfigFileSpecified_Project_dir)
            # print('    potential_path: {}'.format(potential_path))
            return potential_path



# PlatformConfiguration: contains parameters specific to the current running instance of the program, like the project path, the OS it's running on (Mac/Win/Linux), etc.
class PlatformConfiguration(object):
    
    operatingSystem = PlatformOperatingSystem.Unknown
    project_directory = None
    ffmpeg_directory = None
    ffprobe_executable_path_string = None

    is_determined = False


    def __init__(self, parent=None):
        super().__init__(parent=parent)

    # def __init__(self, parent=None):
    #     super().__init__(parent=parent)

    @staticmethod
    def determineOS():
        project_directory_windows = PlatformOperatingSystem.Windows.get_project_directory()
        project_directory_mac = PlatformOperatingSystem.Mac.get_project_directory()

        if (project_directory_windows.exists()):
            # platform is Windows
            PlatformConfiguration.operatingSystem = PlatformOperatingSystem.Windows
            PlatformConfiguration.project_directory = project_directory_windows
        
        elif (project_directory_mac.exists()):
            # platform is Mac
            PlatformConfiguration.operatingSystem = PlatformOperatingSystem.Mac
            PlatformConfiguration.project_directory = project_directory_mac

        else:
            print("ERROR: none of the expected project directories exist!")
            new_user_dir = None
            # Todo: allow user to specify a dir
            if new_user_dir is not None:
                new_user_dir = new_user_dir.resolve()

            PlatformConfiguration.operatingSystem = PlatformOperatingSystem.Unknown
            PlatformConfiguration.project_directory = new_user_dir

        # Using relative ffmpeg path:
        currConfigManagerConfig = ConfigManager().get_config()
        # currConfigFileSpecified_FFMPEG_relative_path = currConfigManagerConfig['DEFAULT']['FFMPEGPath']
        currConfigFileSpecified_FFMPEG_relative_path = currConfigManagerConfig.get('DEFAULT', 'FFMPEGPath', fallback='EXTERNAL/Dependencies/ffmpeg/bin')
        PlatformConfiguration.ffmpeg_directory = PlatformConfiguration.project_directory.joinpath(currConfigFileSpecified_FFMPEG_relative_path)

        # PlatformConfiguration.ffmpeg_directory = PlatformConfiguration.project_directory.joinpath("EXTERNAL", "Dependencies", "ffmpeg", "bin")
        
        if (PlatformConfiguration.ffmpeg_directory.exists()):
            PlatformConfiguration.ffprobe_executable_path_string = str(PlatformConfiguration.ffmpeg_directory.joinpath("ffprobe"))
        else:
            print("ERROR: the ffmpeg path {} doesn't exist! Did you download it from https://ffmpeg.zeranoe.com/builds/ and install it in ./EXTERNAL/Dependencies/ffmpeg?".format(PlatformConfiguration.ffmpeg_directory))
            PlatformConfiguration.ffprobe_executable_path_string = None
            raise FileNotFoundError

        PlatformConfiguration.is_determined = True

    @staticmethod
    def get_ffmpeg_directory():
        if not PlatformConfiguration.is_determined:
            PlatformConfiguration.determineOS()
        
        return PlatformConfiguration.ffmpeg_directory

    @staticmethod
    def get_ffprobe_executable_path_string():
        if not PlatformConfiguration.is_determined:
            PlatformConfiguration.determineOS()
        return PlatformConfiguration.ffprobe_executable_path_string

    @staticmethod
    def get_project_directory():
        if not PlatformConfiguration.is_determined:
            PlatformConfiguration.determineOS()
        return PlatformConfiguration.project_directory

