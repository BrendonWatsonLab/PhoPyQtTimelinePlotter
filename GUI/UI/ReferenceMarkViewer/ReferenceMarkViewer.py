import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir



class ReferenceMarkViewer(QWidget):


    def __init__(self, parent=None):
        super(ReferenceMarkViewer, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/ReferenceMarkViewer/ReferenceMarkViewer.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI


    def initUI(self):
        pass




class ReferenceMarkViewer_DockWidget(QtWidgets.QDockWidget):

    def __init__(self, parent=None):
        super(ReferenceMarkViewer_DockWidget, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/ReferenceMarkViewer/DockWidget_ReferenceMarkViewer.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI


    def initUI(self):
        pass

