# coding: utf-8
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QAbstractItemView, QTableView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog, QInputDialog, QMenu
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool, QItemSelectionModel, QPersistentModelIndex

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
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.display_context_menu)
        # self.table.doubleClicked.connect(self.edit_trial)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.table_selection_model = QItemSelectionModel(self.model)
        self.table.setModel(self.table_selection_model.model())
        self.table.setSelectionModel(self.table_selection_model)
        self.table_selection_model.selectionChanged.connect(self.update_current_record)

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
        

    def handle_add_new_record_pressed(self):
        print("handle_add_new_record_pressed(...)")
        self.create_new_record()
        # newRecord = BehavioralBox()
        # wasInsertSuccess = self.model.insertRecord(-1, newRecord)
        # if (wasInsertSuccess):
        #     print("insert success!")
        #     self.model.submitAll()
        # else:
        #     print("insert failed!")
        #     self.database_rollback()

        # print("done.")


    def display_context_menu(self, pos):
        index = self.table.indexAt(pos)

        self.menu = QMenu()

        # self.edit_action = self.menu.addAction("Edit")
        # self.edit_action.triggered.connect(self.edit_trial)

        self.duplicate_action = self.menu.addAction("Duplicate")
        self.duplicate_action.triggered.connect(self.duplicate_record)
        self.duplicate_action.setEnabled(False)

        self.delete_action = self.menu.addAction("Delete")
        self.delete_action.triggered.connect(self.delete_record)
        self.delete_action.setEnabled(False)

        table_viewport = self.table.viewport()
        self.menu.popup(table_viewport.mapToGlobal(pos))


    def delete_record(self):
        ## TODO: unimplemented
        print("UNIMPLEMENTED!!!")
        # selected_row_index = self.table_selection_model.currentIndex().data(Qt.EditRole)
        index_list = []                                                          
        for model_index in self.table.selectionModel().selectedRows():       
            index = QPersistentModelIndex(model_index)         
            index_list.append(index)                                             

        num_items_to_remove = len(index_list)
        reply = QMessageBox.question(
            self, "Confirm", "Really delete the selected {0} records?".format(num_items_to_remove), QMessageBox.Yes, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for index in index_list:
                self.current_record = self.model.record(index.row())
                self.database_connection.session.delete(self.current_record)
                # self.model.removeRow(index.row())

            # self.database_connection.session.commit()
            # self.model.refresh()

    def duplicate_record(self):
        ## TODO: unimplemented
        print("UNIMPLEMENTED!!!")
        index_list = []                                                          
        for model_index in self.table.selectionModel().selectedRows():       
            index = QPersistentModelIndex(model_index)         
            index_list.append(index)                                             

        num_items_to_remove = len(index_list)
        selected_row_index = None
        # Get only first item
        if (num_items_to_remove > 0):
            print("duplicating!")
            selected_row_index = index_list[0]
            self.current_record = self.model.record(index.row())
            new = self.current_record.duplicate()
            self.database_connection.session.add(new)
            self.database_connection.session.commit()
            self.model.refresh()

        else:
            print("selection empty!")
            return
        
        print("done.")
        

    def create_new_record(self):
        dialog = QInputDialog(self)
        dialog.setLabelText("Please enter the name for the new Record.")
        dialog.textValueSelected.connect(self.store_new_record)
        dialog.exec()

    def store_new_record(self, name):
        rec = BehavioralBox()
        rec.name = name
        
        self.database_connection.session.add(rec)
        self.database_connection.session.commit()
        print("storing new record")
        self.model.refresh()

    def update_current_record(self, x, y):
        self.current_record = self.table_selection_model.currentIndex().data(Qt.EditRole)
