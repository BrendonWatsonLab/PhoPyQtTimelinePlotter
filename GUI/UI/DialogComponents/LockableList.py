# LockableList.py
# Generated from c:\Users\halechr\repo\PhoPyQtTimelinePlotter\GUI\UI\DialogComponents\LockableList.ui automatically by PhoPyQtClassGenerator VSCode Extension
import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QHeaderView
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from GUI.UI.DialogComponents.ListLockableEditButtons_DialogComponents import ListLockableEditButtons_DialogComponents

## IMPORTS:
# from GUI.UI.DialogComponents.LockableList import LockableList

""" LockableList: a list widget with edit controls at the bottom to enable/disable adding/removing items from the list

lblListTitle: the title of the list
listView: the main list (QListView)
listLockableEditWidget: ListLockableEditButtons_DialogComponents

"""
class LockableList(QWidget):

	isEditingChanged = pyqtSignal(bool)
	action_plus_pressed = pyqtSignal()
	action_minus_pressed = pyqtSignal()

	# emitted when the list selection changes. Used to enable/disable the minus button in its listLockableEditWidget and to inform any interested parents
	action_selection_changed = pyqtSignal(int)

	def __init__(self, parent=None):
		super().__init__(parent=parent) # Call the inherited classes __init__ method
		self.ui = uic.loadUi("GUI/UI/DialogComponents/LockableList.ui", self) # Load the .ui file

		self.initUI()
		self.show() # Show the GUI


	def initUI(self):
		self.ui.listLockableEditWidget.isLockedChanged.connect(self.handle_lock_toggled)
		self.ui.listLockableEditWidget.action_plus_pressed.connect(self.handle_plus_button_pressed)
		self.ui.listLockableEditWidget.action_minus_pressed.connect(self.handle_minus_button_pressed)

		pass

	# def __str__(self):
	# 	return 'tEST'


	def set_list_label(self, titleStr):
		self.ui.lblListTitle.setText(titleStr)


	@pyqtSlot()
	def handle_plus_button_pressed(self):
		print("LockableList.handle_plus_button_pressed()")
		self.action_plus_pressed.emit()

	@pyqtSlot()
	def handle_minus_button_pressed(self):
		print("LockableList.handle_minus_button_pressed()")
		self.action_minus_pressed.emit()

	@pyqtSlot(bool)
	def handle_lock_toggled(self, is_checked):
		print("LockableList.handle_lock_toggled(is_checked: {})".format(str(is_checked)))
		is_locked = (not is_checked)
		is_editing = (not is_locked)
		self.isEditingChanged.emit(is_editing)

