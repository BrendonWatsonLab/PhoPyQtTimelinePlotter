import sys
from enum import Enum
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

from GUI.Model.TrackType import TrackType

# FilesystemRecordBase.py
# from app.filesystem.FilesystemRecordBase import *


""" FilesystemRecordBase: an attempt to make a "record" like object for the filesystem analagous to the records loaded from the database

"""
class FilesystemRecordBase(object):

    @staticmethod
    def get_track_type():
        return TrackType.DataFile

