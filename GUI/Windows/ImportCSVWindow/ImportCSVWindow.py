# ImportCSVWindow.py
# Generated from c:\Users\halechr\repo\PhoPyQtTimelinePlotter\GUI\Windows\ImportCSVWindow\ImportCSVWindow.ui automatically by PhoPyQtClassGenerator VSCode Extension
import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QHeaderView, QDialog
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from GUI.UI.ImportCSVWidget.ImportCSVWidget import ImportCSVWidget

## IMPORTS:
# from GUI.Windows.ImportCSVWindow.ImportCSVWindow import ImportCSVWindow


""" 
mainImportCSVWidget

"""
class ImportCSVWindow(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent=parent) # Call the inherited classes __init__ method
		self.ui = uic.loadUi("GUI/Windows/ImportCSVWindow/ImportCSVWindow.ui", self) # Load the .ui file


		self.initUI()
		self.show() # Show the GUI


	def initUI(self):
		# self.mainImportCSVWidget
		pass

