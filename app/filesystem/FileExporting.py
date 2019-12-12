# coding: utf-8
# FileExporting.py
# Written by Pho Hale on 12-12-2019
import sys, os, csv
from datetime import datetime, timezone, timedelta
from enum import Enum
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog, QFileDialog
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QStandardItemModel
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QRunnable

## IMPORTS:
# from app.filesystem.FileExporting import FileExportingMixin


class FileExportingMixin(object):

    
    # The dialog presented when the user pressed "Export File"
    def on_exportFile_selected(self):
        path = QFileDialog.getSaveFileName(self, 'Export Video Events', os.getenv('HOME'), 'CSV(*.csv)')
        return path[0]

        # name = QFileDialog.getSaveFileName(self, 'Save File')
        # file = open(name,'w')
        # text = self.textEdit.toPlainText()
        # file.write(text)
        # file.close()        
        
        return

    # exports the behavior/partition data for a video file given by "videoRecord"
    @staticmethod
    def export_behavior_data_for_video(outputFilePath, videoRecord, partitionsContainerArray):
        
        relevantEvents = []
        # Find events within the timespan of the video
        for aContainerObj in partitionsContainerArray:
            currRecord: CategoricalDurationLabel = aContainerObj.get_record()

            if (currRecord.start_time)

        
        # write to CSV
                
            with open(path[0], 'w', newline='') as csv_file:
                writer = csv.writer(csv_file, dialect='excel')
                for row in range(self.table_contacts.rowCount()):
                    row_data = []
                    for column in range(self.table_contacts.columnCount()):
                        item = self.table_contacts.item(row, column)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    writer.writerow(row_data)


        return