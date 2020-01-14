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

from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors
from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingDialog

from GUI.UI.ImportCSVWidget.ImportCSVWidget import ImportCSVWidget

## IMPORTS:
# from GUI.Windows.ImportCSVWindow.ImportCSVWindow import ImportCSVWindow


""" 
mainImportCSVWidget

"""
class ImportCSVWindow(AbstractDatabaseAccessingDialog):
	def __init__(self, database_connection, parent=None):
		super().__init__(database_connection, parent=parent) # Call the inherited classes __init__ method
		self.ui = uic.loadUi("GUI/Windows/ImportCSVWindow/ImportCSVWindow.ui", self) # Load the .ui file
		self.enable_none_selection = True # if true, an "empty" item is added to the combobox dropdown lists which is selected by default
		self.reloadModelFromDatabase()

		self.initUI()
		self.show() # Show the GUI


	def initUI(self):
		# self.mainImportCSVWidget
		self.ui.mainImportCSVWidget.set_database_connection(self.get_database_connection())
		pass


	# Override:
	def set_database_connection(self, new_db_connection_ref):
		self.database_connection = new_db_connection_ref
		# Set children's database connection too:
		self.ui.mainImportCSVWidget.set_database_connection(new_db_connection_ref)


	# ## Data Model Functions:
	# # Updates the member variables from the database
	# # Note: if there are any pending changes, they will be persisted on this action
	# def reloadModelFromDatabase(self):
	# 	# Load the latest behaviors and colors data from the database
	# 	self.behaviorGroups = self.database_connection.load_behavior_groups_from_database()
	# 	self.behaviors = self.database_connection.load_behaviors_from_database()

	# 	# set_database_connection
	# 	# self.ui.frame_TypeSubtype.setModel(self.behaviorGroups, self.behaviors, self)

