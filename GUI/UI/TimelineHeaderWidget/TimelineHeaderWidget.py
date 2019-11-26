import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

# from app.BehaviorsList import BehaviorsManager, BehaviorInfoOptions
# from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef
# from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors

# from GUI.UI.DialogComponents.DialogComponents_StartEndDate

# from GUI.UI.TimelineHeaderWidget.TimelineHeaderWidget import TimelineHeaderWidget

class TimelineHeaderWidget(QFrame):

    def __init__(self, track_id, track_name, parent=None):
        super(TimelineHeaderWidget, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/TimelineHeaderWidget/TimelineHeaderWidget.ui", self) # Load the .ui file
        self.track_id = track_id
        self.track_name = track_name

        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        # self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)
        self.ui.dockWidget_Main.setWindowTitle(self.track_name)
        self.ui.lblTitle.setText(self.track_name)
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
    
    def set_editable(self, is_editable):
        for aControl in [self.ui.lineEdit_Title, self.ui.lineEdit_Subtitle, self.ui.textBrowser_Body]:
            aControl.setReadOnly(not is_editable)