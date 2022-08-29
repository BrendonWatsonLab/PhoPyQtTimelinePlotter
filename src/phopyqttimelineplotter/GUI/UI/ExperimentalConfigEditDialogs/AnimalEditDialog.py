import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors
from phopyqttimelineplotter.GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingDialog

# When you set a subtype, ensure that its parent is selected as the type
# When you select a type that's incompatible with the current subtype, probably change the subtype to the first of that type

class AnimalEditDialog(AbstractDatabaseAccessingDialog):

     # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal()

     # This defines a signal called 'closed' that takes no arguments.
    on_commit = pyqtSignal(datetime, datetime, datetime, str, str)

    def __init__(self, database_connection, parent=None):
        super(AnimalEditDialog, self).__init__(database_connection, parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/ExperimentalConfigEditDialogs/AnimalEditDialog.ui", self) # Load the .ui file
        self.reloadModelFromDatabase()
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        # self.ui.buttonBox.accepted.connect(self.accept)
        # self.ui.buttonBox.rejected.connect(self.reject)
        pass


## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        pass

    def accept(self):
        print('AnimalEditDialog accept:')
        # Emit the signal.
        self.on_commit.emit(self.get_birth_date(), self.get_receive_date(), self.get_death_date(), self.get_name(), self.get_notes())
        super(AnimalEditDialog, self).accept()

    def reject(self):
        print('AnimalEditDialog reject:')
        self.on_cancel.emit()
        super(AnimalEditDialog, self).reject()





    def set_birth_date(self, birthDate):
        self.ui.dateTimeEdit_Birth.setDateTime(birthDate)

    def set_receive_date(self, receiveDate):
        self.ui.dateTimeEdit_Receive.setDateTime(receiveDate)

    def set_death_date(self, deathDate):
        self.ui.dateTimeEdit_Death.setDateTime(deathDate)

    def get_birth_date(self):
        return self.ui.dateTimeEdit_Birth.dateTime().toPyDateTime()

    def get_receive_date(self):
        return self.ui.dateTimeEdit_Receive.dateTime().toPyDateTime()

    def get_death_date(self):
        return self.ui.dateTimeEdit_Death.dateTime().toPyDateTime()

    # def get_dates(self):
    #     return (self.get_start_date(), self.get_end_date())

    def get_name(self):
        return self.ui.lineEdit_Name.text()
    
    def get_notes(self):
        return self.ui.textBrowser_Notes.toPlainText()

    def set_name(self, updatedStr):
        self.ui.lineEdit_Name.setText(updatedStr)

    def set_notes(self, updatedStr):
        return self.ui.textBrowser_Notes.setPlainText(updatedStr)
    
