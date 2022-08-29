# ImportCSVWidget.py
# Generated from c:\Users\halechr\repo\PhoPyQtTimelinePlotter\GUI\UI\ImportCSVWidget\ImportCSVWidget.ui automatically by PhoPyQtClassGenerator VSCode Extension
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum

import numpy as np
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import (
    QDir,
    QEvent,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFileSystemModel,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from phopyqttimelineplotter.GUI.UI.AbstractDatabaseAccessingWidgets import (
    AbstractDatabaseAccessingWidget,
)
from phopyqttimelineplotter.GUI.UI.DialogComponents.ListLockableEditButtons_DialogComponents import (
    ListLockableEditButtons_DialogComponents,
)

## IMPORTS:
# from phopyqttimelineplotter.GUI.UI.ImportCSVWidget.ImportCSVWidget import ImportCSVWidget

""" ImportCSVWidget: a widget that allows the user to select the context in which the Labjack CSV Data is imported.
importContextMain: ListLockableEditButtons_DialogComponents

"""


class ImportCSVWidget(AbstractDatabaseAccessingWidget):
    def __init__(self, parent=None):
        super().__init__(
            None, parent=parent
        )  # Call the inherited classes __init__ method
        self.ui = uic.loadUi(
            "GUI/UI/ImportCSVWidget/ImportCSVWidget.ui", self
        )  # Load the .ui file

        self.initUI()
        self.show()  # Show the GUI

    def initUI(self):
        # self.importContextMain
        pass

    # Override:
    def set_database_connection(self, new_db_connection_ref):
        self.database_connection = new_db_connection_ref
        # Set children's database connection too:
        self.ui.importContextMain.set_database_connection(new_db_connection_ref)

    # def __str__(self):
    # 	return
