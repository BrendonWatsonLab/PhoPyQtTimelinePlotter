import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QStyle
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

# from GUI.UI.TimelineHeaderWidget.TimelineHeaderWidget import TimelineHeaderWidget

class TimelineHeaderWidget(QFrame):

    toggleCollapsed = pyqtSignal(int, bool)
    showOptions = pyqtSignal(int)
    refresh = pyqtSignal(int)


    def __init__(self, track_id, track_name=None, parent=None):
        super(TimelineHeaderWidget, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/TimelineHeaderWidget/TimelineHeaderWidget.ui", self) # Load the .ui file
        self.track_id = track_id
        if track_name is None:
            self.track_name = "track {0}".format(self.track_id)
        else:
            self.track_name = track_name
        
        # self.setAutoFillBackground(False)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)

        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        # self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)
        self.ui.dockWidget_Main.setWindowTitle(self.track_name)
        self.ui.lblTitle.setText(self.track_name)

        # self.ui.textBrowser_Main.setAutoFillBackground(False)

        # Actions:
        # self.ui.actionToggle_Track_Header_Collapsed.triggered.connect(self.on_collapse_pressed)
        # self.ui.actionShow_Track_Options.triggered.connect(self.on_options_pressed)
        # self.ui.actionRefresh_Track.triggered.connect(self.on_reload_pressed)

        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0,0,0,0)

        self.dockWidgetContents.layout().setSpacing(0)
        self.dockWidgetContents.layout().setContentsMargins(0,0,0,0)
        
        self.ui.frame_TopButtons.setHidden(False)

        self.ui.btnToggleCollapse.setIcon(self.style().standardIcon(QStyle.SP_TitleBarShadeButton))
        self.ui.btnToggleCollapse.setText("")
        # self.ui.toolButton_0.setIcon(self.style().standardIcon(QStyle.SP_TitleBarShadeButton))
        # self.ui.toolButton_0.setDefaultAction(self.ui.actionToggle_Track_Header_Collapsed)
        self.ui.btnToggleCollapse.clicked.connect(self.on_collapse_pressed)

        self.ui.btnOptions.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.ui.btnOptions.setText("")
        # self.ui.toolButton_2.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        # self.ui.toolButton_2.setDefaultAction(self.ui.actionShow_Track_Options)
        self.ui.btnOptions.clicked.connect(self.on_options_pressed)

        self.ui.btnRefresh.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.ui.btnRefresh.setText("")
        # self.ui.toolButton_3.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        # self.ui.toolButton_3.setDefaultAction(self.ui.actionRefresh_Track)
        self.ui.btnRefresh.clicked.connect(self.on_reload_pressed)

        # self.ui.toolButton_0.setEnabled(True)
        # self.ui.toolButton_2.setEnabled(True)
        # self.ui.toolButton_3.setEnabled(True)

        # self.ui.toolButton_0.setHidden(True)
        # self.ui.toolButton_2.setHidden(True)
        # self.ui.toolButton_3.setHidden(True)
        # self.ui.textBrowser_Main

        # self.ui.toolButton_0
        # self.ui.toolButton_1
        # self.ui.toolButton_2
        pass

    def get_title(self):
        return self.ui.lblTitle.text()
    
    def get_body(self):
        return self.ui.textBrowser_Main.toPlainText()

    def set_title(self, updatedStr):
        self.ui.lblTitle.setText(updatedStr)
        self.ui.dockWidget_Main.setWindowTitle(updatedStr)

    def set_body(self, updatedStr):
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
        self.dockWidgetContents.setHidden(True)

    def perform_expand(self):
        self.dockWidgetContents.setHidden(False)
