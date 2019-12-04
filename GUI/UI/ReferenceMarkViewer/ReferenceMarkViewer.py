import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir


class ReferenceMarkViewer(QtWidgets.QDockWidget):

     # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal()

     # This defines a signal called 'closed' that takes no arguments.
    # on_commit = pyqtSignal([datetime, str, str, str], [datetime, datetime, str, str, str])

    on_commit = pyqtSignal([datetime, str, str, str, int, int, int, int], [datetime, datetime, str, str, str, int, int, int, int])


    def __init__(self, parent=None):
        super(ReferenceMarkViewer, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/ReferenceMarkViewer/TeReferenceMarkViewerxtAnnotations.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI


    def initUI(self):
        # self.ui.buttonBox.accepted.connect(self.accept)
        # self.ui.buttonBox.rejected.connect(self.reject)
        pass

