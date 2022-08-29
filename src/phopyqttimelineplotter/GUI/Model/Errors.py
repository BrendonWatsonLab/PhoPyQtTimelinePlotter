#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum

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
    QAbstractScrollArea,
    QAbstractSlider,
    QAction,
    QApplication,
    QDialog,
    QFileSystemModel,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QTreeView,
    QVBoxLayout,
    QWidget,
    qApp,
)

# Errors.py

## IMPORTS:
# from phopyqttimelineplotter.GUI.Model.Errors import SimpleErrorStatusMixin

""" SimpleErrorStatusMixin: a simple string flag that indicates whether a class currently has an error or not.
Requires:
    self._error_string

"""


class SimpleErrorStatusMixin(object):
    error_status_changed = pyqtSignal()  # Called when the "has_error" has changed
    error_string_changed = pyqtSignal()  # Called when the "has_error" has changed

    # Error Status:
    def get_has_error(self):
        return self._error_string is not None

    def get_error_string(self):
        return self._error_string

    # Getters:
    @property
    def has_error(self):
        return self.get_has_error()

    @property
    def error_string(self):
        return self.get_error_string()

    def set_has_error(self, new_error_string):
        prev_has_error = self.get_has_error()
        prev_error_string = self.get_error_string()

        if prev_error_string != new_error_string:
            # Error string changed
            self._error_string = new_error_string
            self.error_string_changed.emit()
            # Check whether the status also changed
            new_has_error = self.get_has_error()
            if prev_has_error != new_has_error:
                # Emit the status changed indicator if the status has changed
                self.error_status_changed.emit()
        else:
            # Otherwise nothing has changed
            pass

        self.error_status_changed.emit()

    @error_string.setter
    def error_string(self, new_value):
        self.set_has_error(new_value)
