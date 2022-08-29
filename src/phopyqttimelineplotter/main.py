import datetime as dt
import pathlib
import sqlite3

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import sqlalchemy as db
from app.database.DatabaseConnectionRef import DatabaseConnectionRef
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import (
    QDir,
    QEvent,
    QObject,
    QPoint,
    QRect,
    QResource,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QStandardItem
from PyQt5.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileSystemModel,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError, OperationalError

from phopyqttimelineplotter.GUI.HelpWindow.HelpWindowFinal import *
from phopyqttimelineplotter.GUI.MainObjectListsWindow.MainObjectListsWindow import *
from phopyqttimelineplotter.GUI.MainWindow.TimelineDrawingWindow import *
from phopyqttimelineplotter.GUI.Model.Events.PhoDurationEvent_Video import (
    PhoDurationEvent_Video,
)
from phopyqttimelineplotter.GUI.Model.Events.PhoEvent import PhoEvent
from phopyqttimelineplotter.GUI.Windows.ExampleDatabaseTableWindow import (
    ExampleDatabaseTableWindow,
)
from phopyqttimelineplotter.GUI.Windows.ImportCSVWindow.ImportCSVWindow import (
    ImportCSVWindow,
)

# from Testing.SqliteEventsDatabase import save_video_events_to_database, load_video_events_from_database


def get_user_home_directory():
    from os import path

    p = pathlib.Path(path.expanduser("~"))
    # Path.home()
    return p


# takes an integer box identifier like '5' and produces 'BB05'
def get_bbIDstring(aBBID, bb_prefix="BB"):
    return "%s{0:02}".format(bb_prefix, aBBID)


# The main application
class TimelineApplication(QApplication):

    shouldShowGUIWindows = True
    shouldShowMainGUIWindow = True
    shouldShowListGUIWindow = False
    shouldShowExampleWindow = False
    shouldShowImportWindow = False  # TODO: this is what I was working on last

    database_file_name = "BehavioralBoxDatabase.db"

    # Attempt to automate box folder generation, but then realized I don't want some of them
    # video_file_search_root = 'E:/Transcoded Videos/' # The folder containing the box folders containg videos
    # bbID_strings = [get_bbIDstring(i) for i in range(17)] # ['BB00', 'BB01', ...]
    # video_file_search_paths = [(TimelineApplication.video_file_search_root + aBBID_String + '/') for aBBID_String in TimelineApplication.bbID_strings]

    video_file_search_paths = ["E:/Transcoded Videos/BB12"]

    # video_file_search_paths = ["E:/Transcoded Videos/BB02", "E:/Transcoded Videos/BB04", "E:/Transcoded Videos/BB06", "E:/Transcoded Videos/BB09", "E:/Transcoded Videos/BB12", "E:/Transcoded Videos/BB14", "E:/Transcoded Videos/BB15", "E:/Transcoded Videos/BB16"]
    # video_file_search_paths = ["O:/Transcoded Videos/BB00", "O:/Transcoded Videos/BB01", "O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]
    # video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]
    # video_file_search_paths = ["O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]

    user_home_path = get_user_home_directory()

    project_directory_windows = pathlib.Path.joinpath(
        user_home_path, "source/repos/PhoPyQtTimelinePlotter/"
    )
    project_directory_mac = pathlib.Path.joinpath(
        user_home_path, "repo/PhoPyQtTimelinePlotter/"
    )

    # project_directory_windows = pathlib.Path.joinpath(user_home_path, "repo/PhoPyQtTimelinePlotter/")
    # project_directory_mac = pathlib.Path.joinpath(user_home_path, "repo/PhoPyQtTimelinePlotter/")

    # C:\Users\watsonlab\source\repos\PhoPyQtTimelinePlotter\lib
    # project_directory_windows = pathlib.Path("C:/Users/halechr/repo/PhoPyQtTimelinePlotter/")
    # project_directory_mac = pathlib.Path("/Users/pho/repo/PhoPyQtTimelinePlotter/")

    @staticmethod
    def get_project_directory():
        if TimelineApplication.project_directory_windows.exists():
            # platform is Windows
            return TimelineApplication.project_directory_windows

        elif TimelineApplication.project_directory_mac.exists():
            # platform is Mac
            return TimelineApplication.project_directory_mac

        else:
            print("WARNING: none of the hard-coded project directories exist!")
            new_user_dir = None
            # Todo: allow user to specify a dir
            # Try CWD:
            new_user_dir = pathlib.Path.cwd()

            if new_user_dir is not None:
                print(
                    "    Using current working path as the project directory ({}).".format(
                        new_user_dir
                    )
                )
                new_user_dir = new_user_dir.resolve()

            return new_user_dir

    def __init__(self, args):
        super(TimelineApplication, self).__init__(args)
        # self.database_file_path = '/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db'
        # self.database_file_path = 'G:\Google Drive\Modern Behavior Box\Results - Data\BehavioralBoxDatabase.db'
        # self.database_file_path = "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db"

        self.project_directory_path = TimelineApplication.get_project_directory()
        self.database_file_parent_path = self.project_directory_path.joinpath(
            "EXTERNAL", "Databases"
        )
        self.database_file_parent_path.mkdir(
            parents=True, exist_ok=True
        )  # make the path if it doesn't exist

        self.database_file_path = self.database_file_parent_path.joinpath(
            TimelineApplication.database_file_name
        )
        self.database_file_path_string = str(self.database_file_path)
        self.video_file_search_paths = TimelineApplication.video_file_search_paths

        try:
            self.database_connection = DatabaseConnectionRef(
                self.database_file_path_string
            )

        except sqlite3.OperationalError as error:
            print(
                "ERROR: database {0} doesn't exist...".format(
                    self.database_file_path_string
                )
            )
            self.database_connection = None
            # fallback_string = '/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db'
            # print("databse {0} doesn't exist... trying {1}...".format(str(self.database_file_path_string), str(fallback_string)))
            # self.database_file_path_string = fallback_string
            # try:
            #     self.database_connection = DatabaseConnectionRef(self.database_file_path_string)
            # except sqlite3.OperationalError as error:
            #     print("file {0} doesn't exist either.".format(str(self.database_file_path_string)))

        except OperationalError as error:
            print(
                "ERROR: database {0} doesn't exist...".format(
                    self.database_file_path_string
                )
            )
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
            print("Showing import window...")
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
            self.mainWindow = TimelineDrawingWindow(
                self.database_connection, self.earliestTime, self.latestTime
            )
            self.windowFlags = self.mainWindow.windowFlags()
            # print(windowFlags)
            self.windowFlags |= (
                Qt.WindowContextHelpButtonHint
            )  # Add the help button to the window
            # mainWindow.setWindowFlags(windowFlags)

            # mainWindow.setWindowFlags(Qt.WindowContextHelpButtonHint) # This works for some reason, but gets rid of the minimize, maximize, and close buttons

        if TimelineApplication.shouldShowListGUIWindow:

            self.mainListWindow = MainObjectListsWindow(
                self.database_connection, self.video_file_search_paths
            )

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
        if (
            TimelineApplication.shouldShowMainGUIWindow
            and TimelineApplication.shouldShowListGUIWindow
        ):
            self.sideListWindowGeometry.moveTopRight(self.mainWindowGeometry.topLeft())
            self.mainListWindow.move(self.sideListWindowGeometry.topLeft())

    @pyqtSlot()
    def on_application_about_to_quit(self):
        print("aboutToQuit")
        self.database_connection.close()
        print("done.")


if __name__ == "__main__":

    QResource.registerResource("data/PhoPyQtTimelinePlotterResourceFile.rcc")

    # create the application and the main window
    app = TimelineApplication(sys.argv)

    # Style
    app.setStyleSheet(open("GUI/application.qss", "r").read())
    # app.setStyleSheet(
    #     "QToolTip { border: 2px solid darkkhaki; padding: 5px; border-radius: 3px; background-color: rgba(255,255,0,0); }");

    # run

    # Connect aboutToQuit signal;
    app.aboutToQuit.connect(app.on_application_about_to_quit)

    sys.exit(app.exec_())
