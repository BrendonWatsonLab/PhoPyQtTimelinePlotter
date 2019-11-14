import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from app.BehaviorsList import BehaviorsManager, BehaviorInfoOptions
from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingDialog

class PartitionEditDialog(AbstractDatabaseAccessingDialog):

     # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal()

     # This defines a signal called 'closed' that takes no arguments.
    on_commit = pyqtSignal(datetime, datetime, str, str, str, int, int)


    def __init__(self):
        super(PartitionEditDialog, self).__init__() # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/PartitionEditDialog/PartitionEditDialog.ui", self) # Load the .ui file
        self.behaviorsManager = BehaviorsManager()
        self.init_from_behaviors_manager()
        self.initUI()
        self.rebuild_combo_boxes_from_behaviors()
        self.show() # Show the GUI

    def initUI(self):
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)
        self.ui.comboBox_Subtype.activated[str].connect(self.on_subtype_combobox_changed)


    def init_from_behaviors_manager(self):
        uniqueBehaviorsList = self.behaviorsManager.get_unique_behaviors()
        uniqueColorsDict = self.behaviorsManager.color_dictionary
        uniqueBehaviorGroupsList = self.behaviorsManager.get_unique_behavior_groups()
        uniqueColorGroupsDict = self.behaviorsManager.groups_color_dictionary

        self.behaviorInfoOptions = []
        self.behaviorInfoGroupsOptions = []
        # Behaviors:
        for (anIndex, aBehavior) in enumerate(uniqueBehaviorsList):
            newObj = BehaviorInfoOptions(aBehavior, aBehavior, anIndex, 0, uniqueColorsDict[aBehavior])
            self.behaviorInfoOptions.append(newObj)
        # Behavior Groups:
        for (anIndex, aBehaviorGroup) in enumerate(uniqueBehaviorGroupsList):
            newGroupObj = BehaviorInfoOptions(aBehaviorGroup, aBehaviorGroup, anIndex, 0, uniqueColorGroupsDict[aBehaviorGroup])
            self.behaviorInfoGroupsOptions.append(newGroupObj)

    # rebuild_combo_boxes_from_behaviors(): rebuilds the two combo boxes from the behaviors
    def rebuild_combo_boxes_from_behaviors(self):
        types_model = self.ui.comboBox_Type.model()
        for (anIndex, aBehaviorInfoGroupOption) in enumerate(self.behaviorInfoGroupsOptions):
            # self.ui.comboBox_Type.addItem(aBehaviorInfoGroupOption.name)
            item = QtGui.QStandardItem(str(aBehaviorInfoGroupOption.name))
            item.setForeground(aBehaviorInfoGroupOption.color)
            types_model.appendRow(item)
            # self.ui.comboBox_Type.addItem(item)
            # self.ui.comboBox_Type.setItemData()

        subtypes_model = self.ui.comboBox_Subtype.model()
        for (anIndex, aBehaviorInfoOption) in enumerate(self.behaviorInfoOptions):
            item = QtGui.QStandardItem(str(aBehaviorInfoOption.name))
            item.setForeground(QtGui.QColor('red'))
            subtypes_model.appendRow(item)

            # self.ui.comboBox_Subtype.addItem(aBehaviorInfoOption.name)

        

    def on_type_combobox_changed(self, text):
        # types changed
        print('type changed: {0}'.format(text))
        #TODO: update avaialable subtypes

    def on_subtype_combobox_changed(self, text):
        print('subtype changed: {0}'.format(text))


    def accept(self):
        print('accept:')
        # Emit the signal.
        self.on_commit.emit(self.get_start_date(), self.get_end_date(), self.get_title(), self.get_subtitle(), self.get_body(),
            self.get_type(), self.get_subtype())
        super(PartitionEditDialog, self).accept()

    def reject(self):
        print('reject:')
        self.on_cancel.emit()
        super(PartitionEditDialog, self).reject()


    def set_type(self, type_id):
        self.ui.comboBox_Type.setCurrentIndex(type_id)
    
    def get_type(self):
        return self.ui.comboBox_Type.currentIndex()

    def set_subtype(self, subtype_id):
        self.ui.comboBox_Subtype.setCurrentIndex(subtype_id)
    
    def get_subtype(self):
        return self.ui.comboBox_Subtype.currentIndex()

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
    
