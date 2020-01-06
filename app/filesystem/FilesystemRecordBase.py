import sys
from enum import Enum
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

from GUI.Model.TrackType import TrackType
from GUI.Model.Events.PhoDurationEvent import PhoDurationEvent, PhoEvent

# FilesystemRecordBase.py
# from app.filesystem.FilesystemRecordBase import FilesystemRecordBase, FilesystemLabjackEvent_Record


""" FilesystemRecordBase: an attempt to make a "record" like object for events loaded from filesystem files analagous to the records loaded from the database

"""
class FilesystemRecordBase(QObject):

    @staticmethod
    def get_track_type():
        return TrackType.DataFile

    def __init__(self, parent=None):
        super().__init__(parent=parent)



""" FilesystemLabjackEvent_Record: for labjack events loaded from a labjack data file

"""
class FilesystemLabjackEvent_Record(FilesystemRecordBase):

    def __init__(self, start_date, end_date, variable_name, variable_color, extended_info_dict, parent=None):
        super().__init__(parent=parent)
        self.start_date = start_date
        self.end_date = end_date
        self.variable_name = variable_name
        self.variable_color = variable_color
        self.extended_info_dict = extended_info_dict


    @staticmethod
    def get_gui_view(aRecord, parent=None):
        currExtraInfoDict = aRecord.extended_info_dict
        outGuiObj = PhoDurationEvent(aRecord.start_date, aRecord.end_date, aRecord.variable_name, aRecord.variable_color, currExtraInfoDict, parent=parent)
        return outGuiObj