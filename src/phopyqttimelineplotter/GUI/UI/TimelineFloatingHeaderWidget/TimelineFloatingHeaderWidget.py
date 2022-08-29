import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QStyle, QDockWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from orangecanvas.gui.dock import CollapsibleDockWidget

from phopyqttimelineplotter.GUI.Model.TrackType import TrackType, TrackConfigMixin
from phopyqttimelineplotter.GUI.Model.TrackConfigs.AbstractTrackConfigs import *
from phopyqttimelineplotter.GUI.Model.TrackConfigs.VideoTrackConfig import *


# from phopyqttimelineplotter.GUI.UI.TimelineFloatingHeaderWidget.TimelineFloatingHeaderWidget import TimelineFloatingHeaderWidget

# TimelineFloatingHeaderWidget: A label that floats over each track in the viewport that scrolls with the user to prevent the user from getting confused as to which track is which
class TimelineFloatingHeaderWidget(TrackConfigMixin, QWidget):
    
    findPrevious = pyqtSignal(int)
    findNext = pyqtSignal(int)
    showOptions = pyqtSignal(int)
    refresh = pyqtSignal(int)


    def __init__(self, track_config, parent=None):
        super(TimelineFloatingHeaderWidget, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/TimelineFloatingHeaderWidget/TimelineFloatingHeaderWidget.ui", self) # Load the .ui file
        self.track_config = track_config
        self.track_id = track_config.get_track_id()
        self.track_name = track_config.get_track_title()

        # self.enableDynamicLabelUpdating: if True, automatically updates the labels from the config. Otherwise relies on the manually set labels
        self.enableDynamicLabelUpdating = True

        # self.setAutoFillBackground(False)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)

        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        self.ui.lblTitle.setText(self.track_name)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0,0,0,0)

        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        
        self.ui.frame_TopButtons.setHidden(False)

        self.ui.btnFindNext.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.ui.btnFindNext.setText("")
        self.ui.btnFindNext.clicked.connect(self.on_find_next_pressed)

        self.ui.btnOptions.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.ui.btnOptions.setText("")
        # self.ui.btnOptions.clicked.connect(self.parent().on_options_pressed)
        self.ui.btnOptions.clicked.connect(self.on_options_pressed)

        self.ui.btnRefresh.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.ui.btnRefresh.setText("")
        self.ui.btnRefresh.clicked.connect(self.on_reload_pressed)

    def get_title(self):
        return self.ui.lblTitle.text()
    
    def set_title(self, updatedStr):
        self.ui.lblTitle.setText(updatedStr)

    def get_subtitle(self):
        return self.ui.lblSubtitle.text()

    def set_subtitle(self, updatedStr):
        return self.ui.lblSubtitle.setText(updatedStr)

    #TrackConfigMixin override
    def get_track_config(self):
        return self.track_config

    def update_from_config(self):
        self.track_id = self.get_track_config().get_track_id()
        self.track_name = self.get_track_config().get_track_title()
        self.set_title(self.get_track_config().get_track_title())
        self.set_subtitle(self.get_track_config().get_track_extended_description())

    def get_config(self):
        return self.get_track_config()

    def set_config(self, newConfig):
        self.track_config = newConfig
        if self.enableDynamicLabelUpdating:
            self.update_labels_dynamically()

    # update_labels_dynamically(): updates the labels dynamically from the active filter
    def update_labels_dynamically(self):
        self.get_track_config().update_labels_dynamically()
        self.update_from_config()
        return

    def on_find_previous_pressed(self):
        print("on_find_previous_pressed(...)")
        self.findPrevious.emit(self.track_id)

    def on_find_next_pressed(self):
        print("on_find_next_pressed(...)")
        self.findNext.emit(self.track_id)

    def on_options_pressed(self):
        print("on_options_pressed(...)")
        self.showOptions.emit(self.track_id)
        
    def on_reload_pressed(self):
        print("on_reload_pressed(...)")
        self.refresh.emit(self.track_id)

