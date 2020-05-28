import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import datetime as dt
import pathlib

import sqlalchemy as db
from sqlalchemy.exc import IntegrityError, OperationalError
import sqlite3
# from Testing.SqliteEventsDatabase import save_video_events_to_database, load_video_events_from_database

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QStyle, QDockWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QResource

from GUI.Model.Events.PhoEvent import PhoEvent
from GUI.Model.Events.PhoDurationEvent_Video import PhoDurationEvent_Video

from GUI.MainWindow.TimelineDrawingWindow import *
from GUI.HelpWindow.HelpWindowFinal import *
from GUI.MainObjectListsWindow.MainObjectListsWindow import *
from GUI.Windows.ExampleDatabaseTableWindow import ExampleDatabaseTableWindow

from GUI.Windows.ImportCSVWindow.ImportCSVWindow import ImportCSVWindow

from app.database.DatabaseConnectionRef import DatabaseConnectionRef
from app.Platform import PlatformOperatingSystem, PlatformConfiguration


##!! IMPORTANT/CONFIGURATION: See app/Platform.py for project and ffprobe path settings


# The main application
class TimelineApplication(QApplication):


    shouldShowGUIWindows = True
    shouldShowMainGUIWindow = True
    shouldShowListGUIWindow = False
    shouldShowExampleWindow = False
    shouldShowImportWindow = False # TODO: this is what I was working on last

    # database_file_name = 'BehavioralBoxDatabase.db'
    database_file_name = 'BehavioralBoxDatabase_Paul.db'
    # should_purge_database = False
    should_purge_database = False # Prompts the user to delete the database



    

    # project_directory_windows = pathlib.Path("C:/Users/halechr/repo/PhoPyQtTimelinePlotter/")
    # project_directory_mac = pathlib.Path("/Users/pho/repo/PhoPyQtTimelinePlotter/")

    # project_directory_windows = PlatformOperatingSystem.Windows.get_project_directory()
    # project_directory_mac = PlatformOperatingSystem.Mac.get_project_directory()

    @staticmethod
    def get_project_directory():
        return PlatformConfiguration.get_project_directory()

    @staticmethod
    def get_ffprobe_executable_path_string():
        return PlatformConfiguration.get_ffprobe_executable_path_string()

            
    def __init__(self, args):
        super(TimelineApplication, self).__init__(args)
        # self.database_file_path = '/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db'
        # self.database_file_path = 'G:\Google Drive\Modern Behavior Box\Results - Data\BehavioralBoxDatabase.db'
        # self.database_file_path = "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db"

        self.project_directory_path = TimelineApplication.get_project_directory()
        self.database_file_parent_path = self.project_directory_path.joinpath("EXTERNAL", "Databases")
        self.database_file_path = self.database_file_parent_path.joinpath(TimelineApplication.database_file_name)
        self.database_file_path_string = str(self.database_file_path)

        if TimelineApplication.should_purge_database:
            print('Warning: Database purging is on!')
            user_response = input("Type 'y' to delete the database, or anything else to continue without deleting it: ")
            if user_response == 'y' or user_response == 'Y':
                if self.database_file_path.exists():
                    self.database_file_path.unlink()
                    print('The database at {} has been purged! Remember to turn it off in main.py if you do not want to be prompted again.'.format(self.database_file_path))

                else:
                    # file didn't exist
                    print("File {} does not exist, so it could not be removed!".format(self.database_file_path))
            else:
                print('Skipping database purge.')

            TimelineApplication.should_purge_database = False



        try:
            self.database_connection = DatabaseConnectionRef(self.database_file_path_string)
            
        except sqlite3.OperationalError as error:
            print("ERROR: databse {0} doesn't exist...".format(self.database_file_path_string))
            self.database_connection = None
            # fallback_string = '/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db'
            # print("databse {0} doesn't exist... trying {1}...".format(str(self.database_file_path_string), str(fallback_string)))
            # self.database_file_path_string = fallback_string
            # try:
            #     self.database_connection = DatabaseConnectionRef(self.database_file_path_string)
            # except sqlite3.OperationalError as error:
            #     print("file {0} doesn't exist either.".format(str(self.database_file_path_string)))

        except OperationalError as error:
            print("ERROR: databse {0} doesn't exist...".format(self.database_file_path_string))
            self.database_connection = None
            # fallback_string = '/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db'
            # print("databse {0} doesn't exist... trying {1}...".format(str(self.database_file_path_string), str(fallback_string)))
            # self.database_file_path_string = fallback_string
            # try:
            #     self.database_connection = DatabaseConnectionRef(self.database_file_path_string)
            # except sqlite3.OperationalError as error:
            #     print("file {0} doesn't exist either.".format(str(self.database_file_path_string)))


        print("done.")

        if TimelineApplication.shouldShowImportWindow:
            print('Showing import window...')
            self.importCSVWindow = ImportCSVWindow(self.database_connection)
            self.importCSVWindow.show()
        

        # Show last 7 days worth of data
        self.earliestTime = dt.datetime.now() - dt.timedelta(days=7)
        self.latestTime = dt.datetime.now()

        # self.video_file_search_paths = ["O:/Transcoded Videos/BB01"]
        # self.video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06"]
        # self.video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]

        if TimelineApplication.shouldShowExampleWindow:
            self.exampleWindow = ExampleDatabaseTableWindow(self.database_connection)

        
        if TimelineApplication.shouldShowMainGUIWindow:
            self.mainWindow = TimelineDrawingWindow(self.database_connection, self.earliestTime, self.latestTime)
            self.windowFlags = self.mainWindow.windowFlags()
            # print(windowFlags)
            self.windowFlags |= Qt.WindowContextHelpButtonHint # Add the help button to the window
            # mainWindow.setWindowFlags(windowFlags)

            # mainWindow.setWindowFlags(Qt.WindowContextHelpButtonHint) # This works for some reason, but gets rid of the minimize, maximize, and close buttons

    
        if TimelineApplication.shouldShowListGUIWindow:
            # self.video_file_search_paths = ["O:/Transcoded Videos/BB00", "O:/Transcoded Videos/BB01", "O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]     
            # self.video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]
            # self.video_file_search_paths = ["O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]
            # self.video_file_search_paths = ["/Users/pho/Desktop/Videos/BB02"]
            self.video_file_search_paths = ["G:/Google Drive/BehavioralBoxData/videos/BB02"]

            self.mainListWindow = MainObjectListsWindow(self.database_connection, self.video_file_search_paths)


        self.desktop = QtWidgets.QApplication.desktop()
        self.resolution = self.desktop.availableGeometry()
        # screen = QDesktopWidget().screenGeometry()

        if TimelineApplication.shouldShowListGUIWindow:
            self.mainListWindow.show()
            self.sideListWindowGeometry = self.mainListWindow.frameGeometry()

        if TimelineApplication.shouldShowMainGUIWindow:
            self.mainWindow.show()
            # hi
            self.mainWindowGeometry = self.mainWindow.frameGeometry()

        if TimelineApplication.shouldShowExampleWindow:
            self.exampleWindow.show()

        # If should show both main and side list GUI
        if (TimelineApplication.shouldShowMainGUIWindow and TimelineApplication.shouldShowListGUIWindow):
            self.sideListWindowGeometry.moveTopRight(self.mainWindowGeometry.topLeft())
            self.mainListWindow.move(self.sideListWindowGeometry.topLeft())

    @pyqtSlot()
    def on_application_about_to_quit(self):
        print("aboutToQuit")
        self.database_connection.close()
        print("done.")



if __name__ == '__main__':

    QResource.registerResource("data/PhoPyQtTimelinePlotterResourceFile.rcc")

    # create the application and the main window
    app = TimelineApplication( sys.argv )

    # Style
    app.setStyleSheet(open("GUI/application.qss", "r").read())
    # app.setStyleSheet(
    #     "QToolTip { border: 2px solid darkkhaki; padding: 5px; border-radius: 3px; background-color: rgba(255,255,0,0); }");

    # run

    # Connect aboutToQuit signal;
    app.aboutToQuit.connect(app.on_application_about_to_quit)

    sys.exit( app.exec_() )
