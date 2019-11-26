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

class DialogComponents_TitleSubtitleBody(QFrame):

    def __init__(self, parent=None):
        super(DialogComponents_TitleSubtitleBody, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/DialogComponents/TitleSubtitleBody_DialogComponents.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        # self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)
        # self.ui.comboBox_Subtype.activated[str].connect(self.on_subtype_combobox_changed)
        pass

    def get_title(self):
        return self.ui.lineEdit_Title.text()
    
    def get_subtitle(self):
        return self.ui.lineEdit_Subtitle.text()

    def get_body(self):
        return self.ui.textBrowser_Body.toPlainText()

    def set_title(self, updatedStr):
        self.ui.lineEdit_Title.setText(updatedStr)

    def set_subtitle(self, updatedStr):
        return self.ui.lineEdit_Subtitle.setText(updatedStr)

    def set_body(self, updatedStr):
        return self.ui.textBrowser_Body.setPlainText(updatedStr)
    