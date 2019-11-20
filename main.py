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
    shouldShowMainGUIWindow = True
    shouldShowListGUIWindow = False

    # Show last 7 days worth of data
    earliestTime = dt.datetime.now() - dt.timedelta(days=7)
    latestTime = dt.datetime.now()
    if (shouldShowGUIWindows):
        # create the application and the main window
        app = QtWidgets.QApplication( sys.argv )

        # database_file_path = '/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db'
        # database_file_path = 'G:\Google Drive\Modern Behavior Box\Results - Data\BehavioralBoxDatabase.db'
        database_file_path = "C:/Users/halechr/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db"
        database_connection = DatabaseConnectionRef(database_file_path)

        # video_file_search_paths = ["O:/Transcoded Videos/BB01"]
        # video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06"]
        # video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]

        
        if shouldShowMainGUIWindow:
            mainWindow = TimelineDrawingWindow(database_connection, earliestTime, latestTime)
            windowFlags = mainWindow.windowFlags()
            # print(windowFlags)
            windowFlags |= Qt.WindowContextHelpButtonHint # Add the help button to the window
            # mainWindow.setWindowFlags(windowFlags)

            # mainWindow.setWindowFlags(Qt.WindowContextHelpButtonHint) # This works for some reason, but gets rid of the minimize, maximize, and close buttons

    
        if shouldShowListGUIWindow:
            video_file_search_paths = ["O:/Transcoded Videos/BB00", "O:/Transcoded Videos/BB01", "O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]     
            # video_file_search_paths = ["O:/Transcoded Videos/BB05", "O:/Transcoded Videos/BB06", "O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]     
            # video_file_search_paths = ["O:/Transcoded Videos/BB08", "O:/Transcoded Videos/BB09"]
            mainListWindow = MainObjectListsWindow(database_connection, video_file_search_paths)


        desktop = QtWidgets.QApplication.desktop()
        resolution = desktop.availableGeometry()
        # screen = QDesktopWidget().screenGeometry()


        # Style
        app.setStyleSheet(open("GUI/application.qss", "r").read())
        # app.setStyleSheet(
        #     "QToolTip { border: 2px solid darkkhaki; padding: 5px; border-radius: 3px; background-color: rgba(255,255,0,0); }");

        # run

        if shouldShowListGUIWindow:
            mainListWindow.show()
            sideListWindowGeometry = mainListWindow.frameGeometry()


        if shouldShowMainGUIWindow:
            mainWindow.show()
            mainWindowGeometry = mainWindow.frameGeometry()

        # If should show both main and side list GUI
        if (shouldShowMainGUIWindow and shouldShowListGUIWindow):
            sideListWindowGeometry.moveTopRight(mainWindowGeometry.topLeft())
            mainListWindow.move(sideListWindowGeometry.topLeft())


        sys.exit( app.exec_() )
