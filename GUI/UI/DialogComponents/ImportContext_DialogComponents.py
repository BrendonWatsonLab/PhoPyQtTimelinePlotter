# ImportContext_DialogComponents.py
# Generated from c:\Users\halechr\repo\PhoPyQtTimelinePlotter\GUI\UI\DialogComponents\ImportContext_DialogComponents.ui automatically by PhoPyQtClassGenerator VSCode Extension
import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QHeaderView
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWidget
from app.database.entry_models.db_model import Animal, VideoFile, BehavioralBox, Context, FileParentFolder, Experiment, Labjack, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent, VideoFile

from GUI.UI.DialogComponents.LockableList import LockableList

## IMPORTS:
# from GUI.UI.DialogComponents import ImportContext_DialogComponents

""" ImportContext_DialogComponents: side-by-side LockableList components
locklist_Box
locklist_Animal
locklist_Cohort

"""
class ImportContext_DialogComponents(AbstractDatabaseAccessingWidget):
	def __init__(self, parent=None):
		super().__init__(None, parent=parent) # Call the inherited classes __init__ method
		self.ui = uic.loadUi("GUI/UI/DialogComponents/ImportContext_DialogComponents.ui", self) # Load the .ui file

		self.initUI()
		self.show() # Show the GUI


	def initUI(self):
		# self.locklist_Box.set_list_label('Box')
		# self.locklist_Animal.set_list_label('Animal')
		# self.locklist_Cohort.set_list_label('Cohort')

		self.locklist_Box.set_record_class(BehavioralBox, 'Box')
		self.locklist_Animal.set_record_class(Animal, 'Animal')
		self.locklist_Cohort.set_record_class(Cohort, 'Cohort')

		pass

	# Override:
	def set_database_connection(self, new_db_connection_ref):
		self.database_connection = new_db_connection_ref
		# Set children's database connection too:
		self.ui.locklist_Box.set_database_connection(new_db_connection_ref)
		self.ui.locklist_Animal.set_database_connection(new_db_connection_ref)
		self.ui.locklist_Cohort.set_database_connection(new_db_connection_ref)

		self.locklist_Box.set_record_class(BehavioralBox, 'Box')
		self.locklist_Animal.set_record_class(Animal, 'Animal')
		self.locklist_Cohort.set_record_class(Cohort, 'Cohort')


	# def __str__(self):
 	# 	return 
