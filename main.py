import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from VideoUtils import findVideoFiles
from TimelinePlotPho import plotTimeline, plot_hlines_Timeline, plot_labjackData_Timeline, plot_combined_timeline
from LabjackEventsLoader import loadLabjackDataFromPhoServerFormat, loadLabjackDataFromMatlabFormat, labjack_variable_names, labjack_variable_colors, labjack_variable_colors_dict, labjack_variable_indicies_dict, labjack_variable_indicies, labjack_variable_event_type, labjack_variable_dispense_type, labjack_variable_port_location, writeLinesToCsvFile
from SqliteEventsDatabase import save_video_events_to_database, load_video_events_from_database

from GUI.PhoEvent import *
from GUI.EventsDrawingWindow import *

if __name__ == '__main__':
    shouldShowGUIWindows = True
    if (shouldShowGUIWindows):
        # create the application and the main window
        app = QtWidgets.QApplication( sys.argv )

        # mainWindow = EventsDrawingWindow(videoEvents, earliestTime, latestTime, dateTimes[relevant_labjack_indicies], dataArray[relevant_labjack_indicies] )
        mainWindow = EventsDrawingWindow(videoFileSearchPaths[0], videoEvents, earliestTime, latestTime, labjackEvents, variableData)
        desktop = QtWidgets.QApplication.desktop()
        resolution = desktop.availableGeometry()

        # Style
        app.setStyleSheet(
            "QToolTip { border: 2px solid darkkhaki; padding: 5px; border-radius: 3px; background-color: rgba(255,255,0,0); }");

        # run
        mainWindow.show()
        sys.exit( app.exec_() )
