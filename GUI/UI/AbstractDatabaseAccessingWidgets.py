# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timezone, timedelta
# import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog

from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef

# An Abstract QMainWindow superclass that holds a reference to an open database
class AbstractDatabaseAccessingWindow(QtWidgets.QMainWindow):
    def __init__(self, database_connection, parent=None):
        super(AbstractDatabaseAccessingWindow, self).__init__(parent) # Call the inherited classes __init__ method
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

    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        pass

    
    # Returns true if any models have pending (uncommited) changes
    def get_has_pending_changes(self):
        return self.database_connection.get_pending_counts().has_pending()
        

            
        


# An Abstract QtWidgets.QDialog superclass that holds a reference to an open database
class AbstractDatabaseAccessingDialog(QtWidgets.QDialog):
    def __init__(self, database_connection, parent=None):
        super(AbstractDatabaseAccessingDialog, self).__init__(parent) # Call the inherited classes __init__ method
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

            
        

