# coding: utf-8
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QTableView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool

from sqlalchemy import Column, ForeignKey, Integer, Table, Text, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.database.entry_models.DatabaseBase import Base, metadata
from pathlib import Path
from datetime import datetime
#(leaves out sqlalchemy & PyQt boilerplate, will not run)
#Define SQL Alchemy model

from GUI.Model.AlchemicalModels.qvariantalchemy import String, Integer, Boolean
from app.database.entry_models.DatabaseBase import Base, metadata
# from sqlalchemy.ext.declarative import declarative_base
# Base = declarative_base()


from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWindow

#create QTable Model/View
from GUI.Model.AlchemicalModels.alchemical_model import SqlAlchemyTableModel

from app.database.entry_models.db_model import Animal, VideoFile, BehavioralBox, Context, FileParentFolder, Experiment, Labjack, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent, VideoFile


class ExampleDatabaseTableWindow(AbstractDatabaseAccessingWindow):
    def __init__(self, database_connection):
        super().__init__(database_connection) # Call the inherited classes __init__ method
        self.reloadModelFromDatabase()

        self.setMouseTracking(True)
        self.initUI()

        
    def initUI(self):
        mainQWidget = QWidget()
        mainLayout= QVBoxLayout()

        # Nested helper function to initialize the menu bar
        def initUI_initMenuBar(self):
            # self.ui.actionLoad.triggered.connect(self.handle_menu_load_event)
            # self.ui.actionSave.triggered.connect(self.handle_menu_save_event)
            # self.ui.actionRefresh.triggered.connect(self.handle_menu_refresh_event)
            pass
            
        desiredWindowWidth = 500
        self.resize( desiredWindowWidth, 800 )

        # Setup the menubar
        initUI_initMenuBar(self)

        # for i in range(5):
        #     exec( 'myGroupBox'+str(i)+'= QGroupBox() ' )
        #     exec( 'myLayout'+str(i)+' = QHBoxLayout()' )       

        #     exec( 'label'+str(i)+'=QLabel("Name '+str(i)+': ")' )
        #     exec( 'self.myLineEdit'+str(i)+'=QLineEdit()' )

        #     exec( 'myLayout'+str(i)+'.addWidget(label'+str(i)+')' )
        #     exec( 'myLayout'+str(i)+'.addWidget(self.myLineEdit'+str(i)+', QtCore.Qt.AlignRight)' )

        #     exec( 'myGroupBox'+str(i)+'.setLayout(myLayout'+str(i)+')' )
        #     exec( 'mainLayout.addWidget(myGroupBox'+str(i)+')' )


        self.table = QTableView(self)
        self.table.setModel(self.model)
        mainLayout.addWidget(self.table)





        self.btnAddNewRecord = QPushButton("New", self)
        self.btnAddNewRecord.released.connect(self.handle_add_new_record_pressed)
        mainLayout.addWidget(self.btnAddNewRecord)

        mainQWidget.setLayout(mainLayout)        
        self.setCentralWidget(mainQWidget) 

        self.table.resizeColumnsToContents()


    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        
        # self.model = self.database_connection.get_animal_table_model()
        # self.model = self.database_connection.get_table_model(FileParentFolder)
        # self.model = self.database_connection.get_table_model(VideoFile)
        self.model = self.database_connection.get_table_model(BehavioralBox)
        

    def handle_add_new_record_pressed(self, button):
        print("handle_add_new_record_pressed(...)")
        newRecord = BehavioralBox()
        wasInsertSuccess = self.model.insertRecord(-1, newRecord)
        if (wasInsertSuccess):
            print("insert success!")
            self.model.submitAll()
        else:
            print("insert failed!")
            self.database_rollback()

        print("done.")
