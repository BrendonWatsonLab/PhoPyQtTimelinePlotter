import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import datetime as dt
# from Testing.SqliteEventsDatabase import save_video_events_to_database, load_video_events_from_database

from GUI.PhoEvent import PhoEvent, PhoDurationEvent
from GUI.TimelineDrawingWindow import *
from GUI.qtimeline import *

if __name__ == '__main__':
    shouldShowGUIWindows = True
    # Show last 7 days worth of data
    earliestTime = dt.datetime.now() - dt.timedelta(days=7)
    latestTime = dt.datetime.now()
    if (shouldShowGUIWindows):
        # create the application and the main window
        app = QtWidgets.QApplication( sys.argv )

        mainWindow = TimelineDrawingWindow(earliestTime, latestTime)
        desktop = QtWidgets.QApplication.desktop()
        resolution = desktop.availableGeometry()

        # Style
        app.setStyleSheet(
            "QToolTip { border: 2px solid darkkhaki; padding: 5px; border-radius: 3px; background-color: rgba(255,255,0,0); }");

        # run
        mainWindow.show()
        sys.exit( app.exec_() )
