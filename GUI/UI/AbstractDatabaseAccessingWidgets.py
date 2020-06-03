# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timezone, timedelta
# import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QMessageBox
from PyQt5.QtCore import QObject

from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef

#from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWidget
# from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingQObject

ShouldCloseConnectionOnlyOnQuit = True

# Displays an interactive message box to prompt the user interactively when there is unsaved database changes
class InteractiveDatabaseCloseMixin(object):
    
    # Called when something requested that the database close.
    # Shows an interactive message box if unsaved changes exist, and lets the user decide whether to save them or just close.
    # returns shouldClose, a Bool indicating whether the user canceled the close event.
    def perform_interactive_database_close(self):
        # Assess whether this is appropriate for a specific widget to have
        user_edited_pending_counts = self.database_connection.get_pending_counts()
        shouldClose = True
        if user_edited_pending_counts.has_pending():
            reply = QMessageBox.question(
                self, "Message",
                "Are you sure you want to quit? Any unsaved work will be lost.",
                QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel,
                QMessageBox.Save)

            if reply == QMessageBox.Close:
                print("User is closing, discarding changes")
                self.database_rollback()
                shouldClose = True
            elif reply == QMessageBox.Cancel:
                print("User canceled closing")
                shouldClose = False
            elif reply == QMessageBox.Save:
                print("User clicked save changes!")
                # Save changes
                print("Saving {0} changes...".format(str(user_edited_pending_counts)))
                self.database_commit()
                shouldClose = True
                pass
            else:
                print("UNIMPLEMENTED: unimplemented message box option!")
                shouldClose = False
                pass

        if shouldClose:
            print("Closing...")
            if (not ShouldCloseConnectionOnlyOnQuit):
                self.database_close()
            else:
                pass # skip closing the database on a window close
        else:
            print("Close has been canceled!")

        return shouldClose


# An Abstract QMainWindow superclass that holds a reference to an open database
class AbstractDatabaseAccessingWindow(InteractiveDatabaseCloseMixin, QtWidgets.QMainWindow):
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

    def database_rollback(self):
        if self.database_connection:
            return self.database_connection.rollback()
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
        
         # Called on close
    def closeEvent(self, event):
        # Assess whether this is appropriate for a specific widget to have
        shouldClose = self.perform_interactive_database_close()
        if shouldClose:
            print("Closing...")
            event.accept()
        else:
            print("Close has been canceled!")
            event.ignore()

            
        


# An Abstract QtWidgets.QDialog superclass that holds a reference to an open database
class AbstractDatabaseAccessingDialog(InteractiveDatabaseCloseMixin, QtWidgets.QDialog):
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

    def database_rollback(self):
        if self.database_connection:
            return self.database_connection.rollback()
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
        
         # Called on close
    def closeEvent(self, event):
        # Assess whether this is appropriate for a specific widget to have
        shouldClose = self.perform_interactive_database_close()
        if shouldClose:
            print("Closing...")
            event.accept()
        else:
            print("Close has been canceled!")
            event.ignore()

            
        


# An Abstract QtWidgets.QWidget superclass that holds a reference to an open database
class AbstractDatabaseAccessingWidget(InteractiveDatabaseCloseMixin, QtWidgets.QWidget):
    def __init__(self, database_connection, parent=None):
        super(AbstractDatabaseAccessingWidget, self).__init__(parent) # Call the inherited classes __init__ method
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

    def database_rollback(self):
        if self.database_connection:
            return self.database_connection.rollback()
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
        
     # Called on close
    def closeEvent(self, event):
        # Assess whether this is appropriate for a specific widget to have
        shouldClose = self.perform_interactive_database_close()
        if shouldClose:
            print("Closing...")
            event.accept()
        else:
            print("Close has been canceled!")
            event.ignore()


      

# An Abstract QtWidgets.QWidget superclass that holds a reference to an open database
class AbstractDatabaseAccessingQObject(QObject):
    def __init__(self, database_connection, parent=None):
        super(AbstractDatabaseAccessingQObject, self).__init__(parent) # Call the inherited classes __init__ method
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

    def database_rollback(self):
        if self.database_connection:
            return self.database_connection.rollback()
        else:
            return False

    def database_close(self):
        if self.database_connection:
            ShouldCloseConnectionOnlyOnQuit
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
