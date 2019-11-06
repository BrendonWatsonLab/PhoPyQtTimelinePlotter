import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.PhoEvent import *

"""
Represents a partition
"""
class PartitionInfo(QObject):
    def __init__(self, name='', start_pos=0.0, end_pos=1.0, extended_data=dict()):
        super(PartitionInfo, self).__init__(None)
        self.name = name
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.extended_data = extended_data

    def __eq__(self, otherEvent):
        return self.name == otherEvent.name and self.start_pos == otherEvent.start_pos and self.end_pos == otherEvent.end_pos

    # Less Than (<) operator
    def __lt__(self, otherEvent):
        return self.start_pos < otherEvent.start_pos

    def __str__(self):
        return 'Event {0}: start_pos: {1}, end_pos: {2}, extended_data: {3}'.format(self.name, self.start_pos, self.end_pos, str(self.extended_data))

"""
A 0.0 to 1.0 timeline
"""
class Partitioner(QObject):

    def __init__(self, totalStartTime, totalEndTime, name='', partitions=None, extended_data=dict()):
        super(Partitioner, self).__init__(None)
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)
        self.name = name
        if partitions:
            self.paritions = partitions
        else:
            self.paritions = [PhoDurationEvent(self.totalStartTime, self.totalEndTime)] # Create default partition
    
        self.extended_data = extended_data

    def __eq__(self, otherEvent):
        return self.name == otherEvent.name and self.totalDuration == otherEvent.totalDuration

    # Less Than (<) operator
    def __lt__(self, otherEvent):
        return self.startTime < otherEvent.startTime

    def __str__(self):
        return 'Event {0}: startTime: {1}, paritions: {2}, extended_data: {3}'.format(self.name, self.paritions, self.color, str(self.extended_data))

