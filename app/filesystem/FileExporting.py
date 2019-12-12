# coding: utf-8
# FileExporting.py
# Written by Pho Hale on 12-12-2019
import sys, os, csv
from datetime import datetime, timezone, timedelta
from enum import Enum
import collections # For ordered dictionarys ()
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog, QFileDialog, QDialog
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QStandardItemModel
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QRunnable, QUrl

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
        # return


    # Prompts the user to select a folder to export files to.
    def on_exportFilesToFolder_selected(self):
        # path = QFileDialog.getExistingDirectory(self, "Select Directory")

        # dialog = QFileDialog(self, 'Select a Folder to Export to', directory)
        dialog = QFileDialog(self, 'Select a Folder to Export to')
        dialog.setOption(QFileDialog.ShowDirsOnly)

        # DontUseNativeDialog
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dialog.setSidebarUrls([QUrl.fromLocalFile("data/")])
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selectedFiles()[0]
        else:
            return ""



        # return path[0]

    # exports the behavior/partition data for a video files given by "videosContainerArray"
    @staticmethod
    def export_behavior_data_for_videos(outputFilePath, videosContainerArray, partitionsContainerArray):
        """
        Note each video 
        Should loop through the partition objects and find all videos that they overlap.
        """
        numPartitionEvents = len(partitionsContainerArray)
        numVideoEvents = len(videosContainerArray)
        # create a dict{int:list} dictionary, with the key being the videoContainerEvent and the list being a list of partition events. Initialize it to an empty list
        # videoFilePartitionArrayMap = {video_event_index:[] for video_event_index in range(numVideoEvents)}
        # videoFilePartitionArrayMap = {aVideoContainerEvent.get_record():[] for aVideoContainerEvent in videosContainerArray}

        # Create an ordered dictionary
        videoFilePartitionArrayMap = collections.OrderedDict([(aVideoContainerEvent.get_record(), []) for aVideoContainerEvent in videosContainerArray])


        # relevantEvents = []
        # Find events within the timespan of the video
        for aContainerObj in partitionsContainerArray:
            # currRecord: CategoricalDurationLabel
            currPartitionRecord = aContainerObj.get_record()
            # Search through all videos to find any that either fully or partially overlap this partition.
            for (aVideoIndex, aVideoContainerObj) in enumerate(videosContainerArray):
                currVideoRecord = aVideoContainerObj.get_record()
                if (currVideoRecord.get_start_date() > currPartitionRecord.get_end_date()):
                    # Partition ends before the video event begins.
                    # This video starts after the end of this partition.
                    # We know that all remaining videos in the list start even later than this one, so there are no more videos in the list that need to be searched. We're done.
                    break
                elif (currPartitionRecord.get_start_date() > currVideoRecord.get_end_date()):
                    # Video ends before the partition even begins (partition is entirely after the video)
                    # This video starts after the end of this partition. We must keep searching the videos.
                    continue
                else:
                    # Otherwise the video either partially or fully overlaps the partition, and it's included
                    # Add it to the partition event objects list for that video file
                    videoFilePartitionArrayMap[currVideoRecord].append(currPartitionRecord)


        # Iterate one more time to produce a streightforward array
        # videoFilePartitionArrayMap

        commaSeparator = ","
        # Iterate through each video and output the partitions that it owns.
        for (aVideoRecord, videoPartitionsList) in videoFilePartitionArrayMap.items():
            partitionString = commaSeparator.join([str(aPartition) for aPartition in videoPartitionsList])
            print("video: {0}, partitions: {1}".format(str(aVideoRecord.file_basename), partitionString ))

            

        
        # write to CSV
                
        # with open(path[0], 'w', newline='') as csv_file:
        #     writer = csv.writer(csv_file, dialect='excel')
        #     for row in range(self.table_contacts.rowCount()):
        #         row_data = []
        #         for column in range(self.table_contacts.columnCount()):
        #             item = self.table_contacts.item(row, column)
        #             if item is not None:
        #                 row_data.append(item.text())
        #             else:
        #                 row_data.append('')
        #         writer.writerow(row_data)


        return