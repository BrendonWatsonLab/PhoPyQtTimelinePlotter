import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import datetime as dt

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
from GUI.Windows.VideoPlayer.MainVideoPlayerWindow import *

from GUI.Model.TrackGroups import VideoTrackGroupSettings, VideoTrackGroup, TrackReference, TrackChildReference, VideoTrackGroupOwningMixin
from app.database.DatabaseConnectionRef import DatabaseConnectionRef

""" IndependentVideoTestApplication: tried to create a new application to test the video player window's thumbnail functionality at home on my mac. 

"""
class IndependentVideoTestApplication(QApplication):

    def __init__(self, args):
        super(IndependentVideoTestApplication, self).__init__(args)

        self.video_file_path = "/Users/pho/Downloads/BehavioralBox_B00_T20190815-0149090099DeepCut_resnet50_real_trainingOct8shuffle1_1030000_labeled.mp4"

        # Show last 7 days worth of data
        self.earliestTime = dt.datetime.now() - dt.timedelta(days=7)
        self.latestTime = dt.datetime.now()

        # Create a new videoPlayerWindow window
        self.videoPlayerWindow = MainVideoPlayerWindow()
        # self.videoPlayerWindow.close_signal.connect(self.on_video_player_window_closed)

        # self.desktop = QtWidgets.QApplication.desktop()
        # self.resolution = self.desktop.availableGeometry()
        # screen = QDesktopWidget().screenGeometry()

        # Set the movie link object
        # currActiveVideoObject = PhoDurationEvent_Video(self.earliestTime, self.latestTime, parent=self.videoPlayerWindow)
        # currActiveTrackRef = TrackReference(-1, -1)
        # currActiveChildRef = TrackChildReference(currActiveTrackRef, -1, currActiveVideoObject, parent=None)

        # newMovieLink = DataMovieLinkInfo(currActiveChildRef, self.videoPlayerWindow, self, parent=self.videoPlayerWindow)
        # self.videoPlayerWindow.set_video_media_link(newMovieLink)

        # self.videoPlayerWindow.show()

    # Called when the video player window closes.
    @pyqtSlot()
    def on_video_player_window_closed(self):
        """ Cleanup the popup widget here """
        print("on_video_player_window_closed()...")
        print("Popup closed.")
        self.videoPlayerWindow = None



    # @pyqtSlot()
    # def on_application_about_to_quit(self):
    #     print("aboutToQuit")
    #     # self.database_connection.close()
    #     print("done.")



if __name__ == '__main__':

    QResource.registerResource("data/PhoPyQtTimelinePlotterResourceFile.rcc")

    # create the application and the main window
    app = IndependentVideoTestApplication( sys.argv )

    # Style
    app.setStyleSheet(open("GUI/application.qss", "r").read())
    # app.setStyleSheet(
    #     "QToolTip { border: 2px solid darkkhaki; padding: 5px; border-radius: 3px; background-color: rgba(255,255,0,0); }");

    # run

    # Connect aboutToQuit signal;
    # app.aboutToQuit.connect(app.on_application_about_to_quit)

    sys.exit( app.exec_() )


