# EventsDrawingWindow.py
# Draws the main window containing several EventTrackDrawingWidgets

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from GUI.EventTrackDrawingWidget import *
from GUI.VideoPostProcessing import show_postprocessing_window

class TimelineDrawingWindow(QtWidgets.QMainWindow):
    TraceCursorWidth = 2
    TraceCursorColor = QColor(51, 255, 102)  # Green

    def __init__(self, filesystemPath, durationEventObjects, totalStartTime, totalEndTime, labjackEventObjects, labjackVariableData=None):
        super(TimelineDrawingWindow, self).__init__()

        self.filesystemPath = filesystemPath
        self.durationEventObjects = durationEventObjects
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.labjackEventObjects = labjackEventObjects
        self.labjackVariableData = labjackVariableData

        if labjackVariableData:
            self.water1_labjackEventObjects = labjackVariableData[0]['variableSpecificEvents']
            self.water2_labjackEventObjects = labjackVariableData[1]['variableSpecificEvents']
            self.food1_labjackEventObjects = labjackVariableData[2]['variableSpecificEvents']
            self.food2_labjackEventObjects = labjackVariableData[3]['variableSpecificEvents']
        else:
            self.water1_labjackEventObjects = np.array(list(filter(lambda obj: obj.name == 'Water1_Dispense', labjackEventObjects)))
            self.water2_labjackEventObjects = np.array(list(filter(lambda obj: obj.name == 'Water2_Dispense', labjackEventObjects)))
            self.food1_labjackEventObjects = np.array(list(filter(lambda obj: obj.name == 'Food1_Dispense', labjackEventObjects)))
            self.food2_labjackEventObjects = np.array(list(filter(lambda obj: obj.name == 'Food2_Dispense', labjackEventObjects)))

        self.initUI()


    # def paintEvent( self, event ):
    #     qp = QtGui.QPainter()
    #     qp.begin( self )
    #     # Draw the trace cursor line
    #     qp.setPen(QtGui.QPen(EventsDrawingWindow.TraceCursorColor, 0.2, join=Qt.MiterJoin))
    #     qp.drawRect(self.cursorX, 0, EventsDrawingWindow.TraceCursorWidth, self.height())
    #     qp.end()

    def get_active_table_rows(self):
        # Find the objects that aren't deemphasized
        activeTableRows = filter(lambda x: (not x.is_deemphasized), self.labjackEventObjects)
        try: import operator
        except ImportError: keyfun = lambda x: x.startTime  # use a lambda if no operator module
        else: keyfun = operator.attrgetter("startTime")  # use operator since it's faster than lambda
        return sorted(activeTableRows, key=keyfun)

    def updateTable(self):
        # Updates the UI table that displays the labjack events and their correspondence to video file times
        # set row count
        activeTableRows = self.get_active_table_rows()
        # self.tableWidget.setRowCount(len(activeTableRows))
        rowCount = 0
        for (labjackPointIndex, currEvent) in enumerate(activeTableRows):
            # For each column
            # currEvent = self.labjackEventObjects[labjackPointIndex]
            self.tableWidget.setItem(labjackPointIndex, 0, QTableWidgetItem(str(currEvent.startTime)))
            self.tableWidget.setItem(labjackPointIndex, 1, QTableWidgetItem(currEvent.name))
            # Get the video-related info
            currVideoIndex = currEvent.extended_data['videoIndex']
            if currVideoIndex:
                cellStr = self.durationEventObjects[currVideoIndex].name
                offsetStr = str(currEvent.extended_data['video_relative_offset'])
            else:
                cellStr = 'None'
                offsetStr = 'None'

            self.tableWidget.setItem(labjackPointIndex, 2, QTableWidgetItem(cellStr))
            self.tableWidget.setItem(labjackPointIndex, 3, QTableWidgetItem(offsetStr))
            rowCount = rowCount + 1

            # for columnIndex in range(0,4):
            #     self.tableWidget.setItem(labjackPointIndex, columnIndex, QTableWidgetItem("Cell"))
        self.tableWidget.setRowCount(rowCount)
        self.tableWidget.scrollToTop()

    def initUIFilesystemTree(self):
        self.model = QFileSystemModel()
        self.model.setRootPath('')
        self.filesystemTree = QTreeView()
        self.filesystemTree.setModel(self.model)

        if self.filesystemPath is not None:
            rootIndex = self.model.index(QDir.cleanPath(self.filesystemPath))
            if rootIndex.isValid():
                self.filesystemTree.setRootIndex(rootIndex)

        self.filesystemTree.setAnimated(False)
        self.filesystemTree.setIndentation(20)
        self.filesystemTree.setSortingEnabled(True)

        #self.filesystemTree.selectionChanged.connect(self.handle_child_selection_event)
        self.filesystemTree.selectionModel().selectionChanged.connect(self.on_video_file_browser_item_click)
        #self.filesystemTree.doubleClicked(
        #self.tableWidget.doubleClicked.connect(self.on_table_item_click)

        self.filesystemTree.setWindowTitle("Dir View")
        self.filesystemTree.resize(640, 480)


    def initUI(self):
        self.resize( 900, 800 )

        self.videoEventsWidget = TimelineTrackDrawingWidget(-1, self.durationEventObjects, [], self.totalStartTime, self.totalEndTime)
        self.videoEventsWidget.selection_changed.connect(self.handle_child_selection_event)
        self.videoEventsWidget.hover_changed.connect(self.handle_child_hover_event)


        self.eventTrackWidgets = [TimelineTrackDrawingWidget(0, [], self.water1_labjackEventObjects, self.totalStartTime, self.totalEndTime),
                                  TimelineTrackDrawingWidget(1, [], self.water2_labjackEventObjects, self.totalStartTime, self.totalEndTime),
                                  TimelineTrackDrawingWidget(2, [], self.food1_labjackEventObjects, self.totalStartTime, self.totalEndTime),
                                  TimelineTrackDrawingWidget(3, [], self.food2_labjackEventObjects, self.totalStartTime, self.totalEndTime)]

        # Build the bottomPanelWidget
        self.labjackEventsContainer = QtWidgets.QWidget()
        self.labjackEventsContainer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.labjackEventsContainer.setAutoFillBackground(True)
        # Debug Pallete
        # p = self.labjackEventsContainer.palette()
        # p.setColor(self.labjackEventsContainer.backgroundRole(), Qt.red)
        # self.labjackEventsContainer.setPalette(p)

        #Layout of Container Widget
        self.vboxLayout = QVBoxLayout(self)
        self.vboxLayout.addStretch(1)
        self.vboxLayout.addSpacing(2.0)
        for i in range(0, len(self.eventTrackWidgets)):
            currWidget = self.eventTrackWidgets[i]
            self.vboxLayout.addWidget(currWidget)
            currWidget.setMinimumSize(500,50)
            currWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            currWidget.mousePressEvent = currWidget.on_button_clicked
            currWidget.mouseReleaseEvent = currWidget.on_button_released

        self.labjackEventsContainer.setLayout(self.vboxLayout)

        self.verticalSplitter = QSplitter(Qt.Vertical)
        self.verticalSplitter.setHandleWidth(8)
        self.verticalSplitter.setMouseTracking(True)
        self.verticalSplitter.addWidget(self.videoEventsWidget)
        self.verticalSplitter.addWidget(self.labjackEventsContainer)

        # Size the widgets
        self.verticalSplitter.setSizes([100, 600])

        # # set the initial scale: 4:1
        # self.verticalSplitter.setStretchFactor(0, 4)
        # self.verticalSplitter.setStretchFactor(1, 1)

        # clickable(self.videoEventsWidget).connect(self.videoEventsWidget.on_button_clicked)
        self.videoEventsWidget.mousePressEvent = self.videoEventsWidget.on_button_clicked
        self.videoEventsWidget.mouseReleaseEvent = self.videoEventsWidget.on_button_released

        # Build the table
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(4)
        # table selection change
        self.tableWidget.doubleClicked.connect(self.on_table_item_click)
        self.updateTable()

        # Build the horizontal splitter
        self.horizontalSplitter = QSplitter(Qt.Horizontal)
        self.horizontalSplitter.setHandleWidth(8)
        self.horizontalSplitter.setMouseTracking(True)
        self.horizontalSplitter.addWidget(self.verticalSplitter)
        self.horizontalSplitter.addWidget(self.tableWidget)

        self.leftmostHorizontalSplitter = QSplitter(Qt.Horizontal)
        self.leftmostHorizontalSplitter.setHandleWidth(8)
        self.leftmostHorizontalSplitter.setMouseTracking(True)
        self.initUIFilesystemTree()
        self.leftmostHorizontalSplitter.addWidget(self.filesystemTree)
        self.leftmostHorizontalSplitter.addWidget(self.horizontalSplitter)



        # Complete setup
        self.setCentralWidget( self.leftmostHorizontalSplitter )
        self.setMouseTracking(True)
        self.statusBar()

        self.setWindowTitle('Pho Events Drawing Window')

        # Cursor tracking
        self.cursorX = 0.0
        self.cursorY = 0.0
        #self.cursorTraceRect = QRect(0,0,0,0)



    def offset_to_percent(self, event_x, event_y):
        percent_x = event_x / self.width()
        percent_y = event_y / self.height()
        return (percent_x, percent_y)

    def offset_to_duration(self, event_x):
        (percent_x, percent_y) = self.offset_to_percent(event_x, 0.0)
        return (self.videoEventsWidget.totalDuration * percent_x)

    def offset_to_datetime(self, event_x):
        duration_offset = self.offset_to_duration(event_x)
        return (self.videoEventsWidget.totalStartTime + duration_offset)

    def keyPressEvent(self, event):
        self.videoEventsWidget.keyPressEvent(event)

    def mouseMoveEvent(self, event):
        self.cursorX = event.x()
        self.cursorY = event.y()
        duration_offset = self.offset_to_duration(self.cursorX)
        datetime = self.offset_to_datetime(self.cursorX)
        text = "window x: {0},  duration: {1}, datetime: {2}".format(self.cursorX, duration_offset, datetime)
        self.videoEventsWidget.on_mouse_moved(event)
        potentially_hovered_child_object = self.videoEventsWidget.hovered_object
        if potentially_hovered_child_object:
            relative_duration_offset = potentially_hovered_child_object.compute_relative_offset_duration(datetime)
            text = text + ' -- relative to duration: {0}'.format(relative_duration_offset)

        self.statusBar().showMessage(text)

    # @pyqtSlot(int, int)
    # Occurs when the user selects an object in the video track with the mouse
    def handle_child_selection_event(self, trackIndex, trackObjectIndex):
        text = "handle_child_selection_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
        # print(text)
        if trackIndex == -1:
            # If it's the video track
            if trackObjectIndex == -1:
                # No selection, just clear the filters
                for i in range(0, len(self.eventTrackWidgets)):
                    currWidget = self.eventTrackWidgets[i]
                    currWidget.set_active_filter(self.totalStartTime, self.totalEndTime)
            else:
                # Get the selected video object
                currHoveredObject = self.videoEventsWidget.hovered_object
                for i in range(0, len(self.eventTrackWidgets)):
                    currWidget = self.eventTrackWidgets[i]
                    currWidget.set_active_filter(currHoveredObject.startTime, currHoveredObject.endTime)

        self.updateTable()

    # Occurs when the user selects an object in the video track with the mouse
    def handle_child_hover_event(self, trackIndex, trackObjectIndex):
        text = "handle_child_hover_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
        # print(text)

    def refresh_child_widget_display(self):
        for i in range(0, len(self.eventTrackWidgets)):
            currWidget = self.eventTrackWidgets[i]
            currWidget.update()

    @pyqtSlot()
    def on_table_item_click(self):
        print("\n")
        # Get the items that make up the table
        activeTableRows = self.get_active_table_rows()
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())
            currObject = activeTableRows[currentQTableWidgetItem.row()]
            currObject.is_emphasized = True
            # TODO: flash the emphasis on and then off to display the item?

        self.refresh_child_widget_display()

    @pyqtSlot()
    def on_video_file_browser_item_click(self):
        print("\n")
        print('on_video_file_browser_item_click!')
        # Get the items that make up the table
        activeTableRows = self.filesystemTree.selectedIndexes()
        if activeTableRows:
            # Get the selected file:
            selectedFilePath = self.filesystemTree.model().data(activeTableRows[0])
            # Returns 'BehavioralBox_B01_T20190929-1354060018.mp4'
            print('selected: ', selectedFilePath)
            found_selected_index = None
            for i, j in enumerate(self.durationEventObjects):
                if j.name == selectedFilePath:
                    found_selected_index = i
                    print('Found matching item with index ', found_selected_index)
                    break

            if found_selected_index:
                selected_object = self.durationEventObjects[found_selected_index]
                final_selected_path = selected_object.extended_data['fullpath']
                print('Final selected path: ', final_selected_path)
                show_postprocessing_window(final_selected_path)
            else:
                print('Failed to find matching object in durationEventObjects matching name ', selectedFilePath)






    # def handle_child_selection_event(self, trackIndex, trackObjectIndex):
    #     text = "handle_child_selection_event(...): trackIndex: {0}, trackObjectIndex: {1}".format(trackIndex, trackObjectIndex)
    #     # print(text)
    #     if trackIndex == -1:
    #         # If it's the video track
    #         if trackObjectIndex == -1:
    #             # No selection, just clear the filters
    #             for i in range(0, len(self.eventTrackWidgets)):
    #                 currWidget = self.eventTrackWidgets[i]
    #                 currWidget.set_active_filter(self.totalStartTime, self.totalEndTime)
    #         else:
    #             # Get the selected video object
    #             currHoveredObject = self.videoEventsWidget.hovered_object
    #             for i in range(0, len(self.eventTrackWidgets)):
    #                 currWidget = self.eventTrackWidgets[i]
    #                 currWidget.set_active_filter(currHoveredObject.startTime, currHoveredObject.endTime)
    #
    #     self.updateTable()