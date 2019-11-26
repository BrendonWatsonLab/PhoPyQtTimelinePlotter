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

from GUI.Model.Filters import *


# from GUI.UI.TimelineHeaderWidget.TimelineHeaderWidget import TimelineHeaderWidget

# _ContentsExpanded
# TimelineHeaderWidget_ContentsExpanded.ui
# TimelineHeaderWidget_ContentsCollapsed.ui


class TimelineHeaderWidget_ContentsCollapsed(QWidget):
    def __init__(self, parent=None):
        super(TimelineHeaderWidget_ContentsCollapsed, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/TimelineHeaderWidget/TimelineHeaderWidget_ContentsCollapsed.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)


class TimelineHeaderWidget_ContentsExpanded(QWidget):
    def __init__(self, parent=None):
        super(TimelineHeaderWidget_ContentsExpanded, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/TimelineHeaderWidget/TimelineHeaderWidget_ContentsExpanded.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        self.ui.lblTitle.setText(self.parent().track_name)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0,0,0,0)

        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        
        self.ui.frame_TopButtons.setHidden(False)

        self.ui.btnToggleCollapse.setIcon(self.style().standardIcon(QStyle.SP_TitleBarShadeButton))
        self.ui.btnToggleCollapse.setText("")
        self.ui.btnToggleCollapse.clicked.connect(self.parent().on_collapse_pressed)

        self.ui.btnOptions.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.ui.btnOptions.setText("")
        self.ui.btnOptions.clicked.connect(self.parent().on_options_pressed)

        self.ui.btnRefresh.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.ui.btnRefresh.setText("")
        self.ui.btnRefresh.clicked.connect(self.parent().on_reload_pressed)

    def get_title(self):
        return self.ui.lblTitle.text()
    
    def get_body(self):
        return self.ui.textBrowser_Main.toPlainText()

    def set_title(self, updatedStr):
        self.ui.lblTitle.setText(updatedStr)

    def set_body(self, updatedStr):
        return self.ui.textBrowser_Main.setPlainText(updatedStr)


class TimelineHeaderWidget(QFrame):

    toggleCollapsed = pyqtSignal(int, bool)
    showOptions = pyqtSignal(int)
    refresh = pyqtSignal(int)


    def __init__(self, track_config, parent=None):
        super(TimelineHeaderWidget, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/TimelineHeaderWidget/TimelineHeaderWidget.ui", self) # Load the .ui file
        self.track_config = track_config
        self.track_id = track_config.get_track_id()
        self.track_name = track_config.get_track_title()
        
        # if track_name is None:
        #     self.track_name = "track {0}".format(self.track_id)
        # else:
        #     self.track_name = track_name
        
        # self.setAutoFillBackground(False)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)

        self.timelineHeaderWidget_ContentsCollapsed = TimelineHeaderWidget_ContentsCollapsed(self)
        self.timelineHeaderWidget_ContentsExpanded = TimelineHeaderWidget_ContentsExpanded(self)

        self.timelineHeaderWidget_ContentsExpanded.set_title(self.track_config.get_track_title())
        self.timelineHeaderWidget_ContentsExpanded.set_body(self.track_config.get_track_extended_description())

        self.initUI()
        self.show() # Show the GUI

    def initUI(self):

        self.ui.dockWidget_Main = CollapsibleDockWidget(parent=self)
        self.ui.dockWidget_Main.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.ui.dockWidget_Main.setFeatures(self.ui.dockWidget_Main.features()|QDockWidget.DockWidgetVerticalTitleBar)
        self.ui.dockWidget_Main.setWindowTitle(self.track_name)
        self.layout().addWidget(self.ui.dockWidget_Main)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)

        self.ui.dockWidget_Main.setCollapsedWidget(self.timelineHeaderWidget_ContentsCollapsed)
        self.ui.dockWidget_Main.setExpandedWidget(self.timelineHeaderWidget_ContentsExpanded)



        # self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)

        # self.ui.dockWidget_Main.setWindowTitle(self.track_name)
        # self.ui.dockWidget_Main.setAttribute(Qt.WA_WState_ExplicitShowHide)
        # self.ui.lblTitle.setText(self.track_name)

        # self.verticalLayout.setSpacing(0)
        # self.verticalLayout.setContentsMargins(0,0,0,0)

        # self.dockWidgetContents.layout().setSpacing(0)
        # self.dockWidgetContents.layout().setContentsMargins(0,0,0,0)
        
        # self.ui.frame_TopButtons.setHidden(False)

        # self.ui.btnToggleCollapse.setIcon(self.style().standardIcon(QStyle.SP_TitleBarShadeButton))
        # self.ui.btnToggleCollapse.setText("")
        # self.ui.btnToggleCollapse.clicked.connect(self.on_collapse_pressed)

        # self.ui.btnOptions.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        # self.ui.btnOptions.setText("")
        # self.ui.btnOptions.clicked.connect(self.on_options_pressed)

        # self.ui.btnRefresh.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        # self.ui.btnRefresh.setText("")
        # self.ui.btnRefresh.clicked.connect(self.on_reload_pressed)

        pass

    def update_from_config(self):
        self.track_id = self.track_config.get_track_id()
        self.track_name = self.track_config.get_track_title()
        self.set_title(self.track_config.get_track_title())
        self.set_body(self.track_config.get_track_extended_description())

    def get_config(self):
        return self.track_config

    def get_title(self):
        return self.ui.lblTitle.text()
    
    def get_body(self):
        return self.ui.textBrowser_Main.toPlainText()

    def set_title(self, updatedStr):
        self.track_config.track_name = updatedStr
        self.ui.lblTitle.setText(updatedStr)
        self.ui.dockWidget_Main.setWindowTitle(updatedStr)

    def set_body(self, updatedStr):
        self.track_config.trackExtendedDescription = updatedStr
        return self.ui.textBrowser_Main.setPlainText(updatedStr)
    
    def on_collapse_pressed(self):
        print("on_collapse_pressed(...)")
        self.toggleCollapsed.emit(self.track_id, False)

    def on_options_pressed(self):
        print("on_options_pressed(...)")
        self.showOptions.emit(self.track_id)
        
    def on_reload_pressed(self):
        print("on_reload_pressed(...)")
        self.refresh.emit(self.track_id)
        
    def perform_collapse(self):
        # self.dockWidgetContents.setHidden(True)
        self.ui.dockWidget_Main.hide()

    def perform_expand(self):
        self.dockWidgetContents.setHidden(False)
