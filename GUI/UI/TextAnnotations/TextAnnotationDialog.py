import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from GUI.UI.DialogComponents.AbstractDialogMixins import BoxExperCohortAnimalIDsFrame_Mixin, ObjectSpecificDialogMixin, DialogObjectIdentifier

class TextAnnotationDialog(ObjectSpecificDialogMixin, BoxExperCohortAnimalIDsFrame_Mixin, QtWidgets.QDialog):

     # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal(DialogObjectIdentifier)

     # This defines a signal called 'closed' that takes no arguments.
    # on_commit = pyqtSignal([datetime, str, str, str], [datetime, datetime, str, str, str])

    on_commit = pyqtSignal([DialogObjectIdentifier, datetime, str, str, str, int, int, int, int], [DialogObjectIdentifier, datetime, datetime, str, str, str, int, int, int, int])


    def __init__(self):
        super(TextAnnotationDialog, self).__init__() # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/TextAnnotations/TextAnnotations.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI


    def initUI(self):
        pass


    def accept(self):
        print('accept:')
        # Emit the signal.
        behavioral_box_id, experiment_id, cohort_id, animal_id = self.frame_BoxExperCohortAnimalIDs.get_id_values(shouldReturnNoneTypes=False)
        if (self.get_end_date()):
            self.on_commit[DialogObjectIdentifier, datetime, datetime, str, str, str, int, int, int, int].emit(self.get_referred_object_identifier(), self.get_start_date(), self.get_end_date(), self.get_title(), self.get_subtitle(), self.get_body(), behavioral_box_id, experiment_id, cohort_id, animal_id)
        else:
            self.on_commit[DialogObjectIdentifier, datetime, str, str, str, int, int, int, int].emit(self.get_referred_object_identifier(), self.get_start_date(), self.get_title(), self.get_subtitle(), self.get_body(), behavioral_box_id, experiment_id, cohort_id, animal_id)
            
        super(TextAnnotationDialog, self).accept()

    def reject(self):
        print('reject:')
        self.on_cancel.emit(self.get_referred_object_identifier())
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

    def set_title(self, updatedStr):
        self.ui.lineEdit_Title.setText(updatedStr)

    def set_subtitle(self, updatedStr):
        return self.ui.lineEdit_Subtitle.setText(updatedStr)

    def set_body(self, updatedStr):
        return self.ui.textBrowser_Body.setPlainText(updatedStr)
    