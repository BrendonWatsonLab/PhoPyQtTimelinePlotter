import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import datetime as dt
# from Testing.SqliteEventsDatabase import save_video_events_to_database, load_video_events_from_database

from GUI.Model.PhoEvent import PhoEvent
from GUI.Model.PhoDurationEvent import PhoDurationEvent

from GUI.MainWindow.TimelineDrawingWindow import *
from GUI.HelpWindow.HelpWindowFinal import *
from GUI.MainObjectListsWindow.MainObjectListsWindow import *

from app.database.DatabaseConnectionRef import DatabaseConnectionRef


if __name__ == '__main__':
    shouldShowGUIWindows = True
    # Show last 7 days worth of data
    earliestTime = dt.datetime.now() - dt.timedelta(days=7)
    latestTime = dt.datetime.now()
    if (shouldShowGUIWindows):
        # create the application and the main window
        app = QtWidgets.QApplication( sys.argv )

        database_file_path = '/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db'
        # database_file_path = 'G:\Google Drive\Modern Behavior Box\Results - Data\BehavioralBoxDatabase.db'
        database_file_path = "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db"
        database_connection = DatabaseConnectionRef(database_file_path)

        # video_file_search_paths = ["O:/Transcoded Videos/BB01"]
        # video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06"]
        video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]

        


        
        mainWindow = TimelineDrawingWindow(database_connection, earliestTime, latestTime)
        mainListWindow = MainObjectListsWindow(database_connection, video_file_search_paths)
        windowFlags = mainWindow.windowFlags()
        # print(windowFlags)
        windowFlags |= Qt.WindowContextHelpButtonHint # Add the help button to the window
        # mainWindow.setWindowFlags(windowFlags)

        # mainWindow.setWindowFlags(Qt.WindowContextHelpButtonHint) # This works for some reason, but gets rid of the minimize, maximize, and close buttons

        desktop = QtWidgets.QApplication.desktop()
        resolution = desktop.availableGeometry()
        # screen = QDesktopWidget().screenGeometry()


        # Style
        app.setStyleSheet(
            "QToolTip { border: 2px solid darkkhaki; padding: 5px; border-radius: 3px; background-color: rgba(255,255,0,0); }");

        # run


        mainListWindow.show()
        mainWindow.show()

        mainWindowGeometry = mainWindow.frameGeometry()
        sideListWindowGeometry = mainListWindow.frameGeometry()

        sideListWindowGeometry.moveTopRight(mainWindowGeometry.topLeft())
        # mainListWindow.moveTopRight(mainWindowGeometry.topLeft())
        mainListWindow.move(sideListWindowGeometry.topLeft())

        sys.exit( app.exec_() )
