import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize


# ModelViewContainer: a simple container used by the timeline tracks that holds a reference to both the view and data objects
#TODO: could extend the GUI partition view object to hold the actual record. This makes the most sense, as they have many overlapping properties that are duplicated.
class ModelViewContainer(QObject):
    def __init__(self, record, view, parent=None):
        super().__init__(parent)
        self.record = record
        self.view = view

    def get_record(self):
        return self.record
    
    def get_view(self):
        return self.view

    

# # Partition: a simple container used by Partitioner that holds a reference to both the view and data objects
# class Partition(ModelViewContainer):
#     def __init__(self, record, view, parent=None):
#         super().__init__(record, view, parent)

