#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMouseEvent

from PyQt5.QtWidgets import QHeaderView, QTableView


class TimestampTableView(QTableView):
    doubleClicked = pyqtSignal(QMouseEvent)

    def __init__(self, parent=None):
        super(TimestampTableView, self).__init__(parent)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def mouseReleaseEvent(self, event):
        super(TimestampTableView, self).mouseReleaseEvent(event)
        index = self.indexAt(event.pos())
        if not index.isValid():
            self.selectionModel().clearSelection()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(event)
