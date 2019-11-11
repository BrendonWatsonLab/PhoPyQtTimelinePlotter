import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

class TextAnnotationDialog(QtWidgets.QDialog):

     # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal()

     # This defines a signal called 'closed' that takes no arguments.
    on_commit = pyqtSignal(datetime, datetime, str, str, str)


    def __init__(self):
        super(TextAnnotationDialog, self).__init__() # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/TextAnnotations/TextAnnotations.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI


    def initUI(self):
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)


    def accept(self):
        print('accept:')
        # Emit the signal.
        self.on_commit.emit(self.get_start_date(), self.get_end_date(), self.get_title(), self.get_subtitle(), self.get_body())
        super(TextAnnotationDialog, self).accept()

    def reject(self):
        print('reject:')
        self.on_cancel.emit()
        super(TextAnnotationDialog, self).reject()

    def set_start_date(self, startDate):
        self.ui.dateTimeEdit_Start.setDateTime(startDate)

    def set_end_date(self, endDate):
        self.ui.checkBox_ShouldUseEndDate.setChecked(True)
        self.ui.dateTimeEdit_End.setDateTime(endDate)

    def get_enable_end_date(self):
        return self.ui.checkBox_ShouldUseEndDate.isChecked()
    
    def get_start_date(self):
        return self.ui.dateTimeEdit_Start.dateTime().toPyDateTime()

    def get_end_date(self):
        if (self.get_enable_end_date()):
            return self.ui.dateTimeEdit_End.dateTime().toPyDateTime()
        else:
            return None

    def get_dates(self):
        return (self.get_start_date(), self.get_end_date())

    def get_title(self):
        return self.ui.lineEdit_Title.text()
    
    def get_subtitle(self):
        return self.ui.lineEdit_Subtitle.text()

    def get_body(self):
        return self.ui.textBrowser_Body.toPlainText()