
# FilesystemOperations.py

import sys
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool

# INCLUDES:
# from app.filesystem.FilesystemOperations import OperationTypes, PendingFilesystemOperation


class OperationTypes(Enum):
        NoOperation = 1
        FilesystemFileFind = 2
        FilesystemMetadataLoad = 3
        FilesystemThumbnailGeneration = 4

class PendingFilesystemOperation(QObject):

    def __init__(self, operation_type=OperationTypes.NoOperation, end_num = 0, start_num = 0, parent=None):
        super().__init__(parent=parent)
        self.operation_type = operation_type
        self.end_num = end_num
        self.start_num = 0

    def restart(self, op_type, end_num):
        self.operation_type = op_type
        self.end_num = end_num
        self.start_num = 0

    # updates with the percent value
    def update(self, new_percent):
        newVal = (float(new_percent) * float(self.end_num))
        self.start_num = newVal

    def get_fraction(self):
        if self.end_num > 0:
            return (float(self.start_num)/float(self.end_num))
        else:
            return 0.0

    def get_percent(self):
        return (self.get_fraction()*100.0)

    def is_finished(self):
        if self.end_num > 0:
            return (self.start_num == self.end_num)
        else:
            return False

