# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timezone, timedelta
# import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog, QTreeWidget, QTreeWidgetItem

# An Abstract QMainWindow superclass that holds a reference to an open database
class AbstractDatabaseAccessingWindow(QtWidgets.QMainWindow):
    def __init__(self, database_connection):
        super(AbstractDatabaseAccessingWindow, self).__init__() # Call the inherited classes __init__ method
        self.database_connection = database_connection

    def get_database_connection(self):
        return self.database_connection

    def set_database_connection(self, new_db_connection_ref):
        # TODO: close the old one?
        self.database_connection = new_db_connection_ref

    def database_commit(self):
        if self.database_connection:
            return self.database_connection.commit()
        else:
            return False

    def database_close(self):
        if self.database_connection:
            self.database_connection.close()
            return True
        else:
            return False

            
        


