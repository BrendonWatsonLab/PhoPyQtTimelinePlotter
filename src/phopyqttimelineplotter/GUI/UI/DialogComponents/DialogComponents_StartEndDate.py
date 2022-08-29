import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

# from phopyqttimelineplotter.GUI.UI.DialogComponents.DialogComponents_StartEndDate import DialogComponents_StartEndDate

class DialogComponents_StartEndDate(QFrame):

    def __init__(self, parent=None):
        super(DialogComponents_StartEndDate, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/DialogComponents/StartEndDate_DialogComponents.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        pass

    def set_start_date(self, startDate):
        self.ui.dateTimeEdit_Start.setDateTime(startDate)

    def set_end_date(self, endDate):
        self.ui.dateTimeEdit_End.setDateTime(endDate)

    def get_start_date(self):
        return self.ui.dateTimeEdit_Start.dateTime().toPyDateTime()

    def get_end_date(self):
        return self.ui.dateTimeEdit_End.dateTime().toPyDateTime()

    def get_dates(self):
        return (self.get_start_date(), self.get_end_date())

    def set_editable(self, is_editable):
        for aControl in [self.ui.dateTimeEdit_Start, self.ui.dateTimeEdit_End]:
            aControl.setReadOnly(not is_editable)
