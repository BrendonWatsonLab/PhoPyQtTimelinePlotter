# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
import time
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from lib.pg_time_axis import DateAxisItem

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import TimelineTrackDrawingWidgetBase, ItemSelectionOptions
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_SelectionBase import TimelineTrackDrawingWidget_SelectionBase

from GUI.Model.Events.PhoDurationEvent_AnnotationComment import *
from GUI.UI.TextAnnotations.TextAnnotationDialog import *

from app.database.SqlAlchemyDatabase import create_TimestampedAnnotation, convert_TimestampedAnnotation, modify_TimestampedAnnotation, modify_TimestampedAnnotation_startDate, modify_TimestampedAnnotation_endDate

from GUI.Model.TrackType import TrackType, TrackConfigMixin, TrackConfigDataCacheMixin


"""
    This track draws a data file (.csv labjack file, for example) as a series of events along the timeline.
"""
class TimelineTrackDrawingWidget_DataFile(TrackConfigDataCacheMixin, TrackConfigMixin, TimelineTrackDrawingWidget_SelectionBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.SingleSelection

    def __init__(self, trackConfig, totalStartTime, totalEndTime, database_connection, parent=None, wantsKeyboardEvents=False, wantsMouseEvents=True):
        self.trackConfig = trackConfig
        super(TimelineTrackDrawingWidget_DataFile, self).__init__(trackConfig.get_track_id(), totalStartTime, totalEndTime, [], database_connection=database_connection, parent=parent, wantsKeyboardEvents=wantsKeyboardEvents, wantsMouseEvents=wantsMouseEvents)
        # self.durationObjects = durationObjects
        self.instantaneousObjects = []
        # self.eventRect = np.repeat(QRect(0,0,0,0), len(durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0,0,0,0), len(self.instantaneousObjects))
        
        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        self.hovered_duration_object_indicies = []

        # Selected Object
        self.selected_duration_object_indicies = []
        self.shouldDismissSelectionUponMouseButtonRelease = TimelineTrackDrawingWidget_DataFile.default_shouldDismissSelectionUponMouseButtonRelease
        self.itemSelectionMode = TimelineTrackDrawingWidget_DataFile.default_itemSelectionMode
        self.itemHoverMode = TimelineTrackDrawingWidget_SelectionBase.default_itemHoverMode

        # Setup Layout
        self.setLayout(QVBoxLayout())
        self.build_child_graph_widget()

        self.setMouseTracking(True)

        self.trackConfig.cacheUpdated.connect(self.on_reloadModelFromConfigCache)
        self.reloadModelFromDatabase()
        self.update_child_graph_widget()
        

    # Override: TrackConfigDataCacheMixin
   # performReloadConfigCache(...): actually tells the config cache to update
    @pyqtSlot()
    def performReloadConfigCache(self):
        #TODO: figure out how to pass file path
        self.get_track_config().reload(self.database_connection.get_session(), self)
    
    
    ## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        # tempAllAnnotationDataObjects = self.database_connection.load_annotation_events_from_database()
        # self.durationRecords = self.trackConfig.filter_records(self.database_connection.get_session())
        # Clear previous stuff before switching
        self.reset_on_reload()

        self.performReloadConfigCache()
        self.update()

    # on_reloadModelFromConfigCache(...): called when the config cache updates to reload the widget
    @pyqtSlot()
    def on_reloadModelFromConfigCache(self):
        # print("TimelineTrackDrawingWidget_DataFile.reloadModelFromConfigCache()")
        # TODO: close any open dialogs, etc, etc
        self.reset_on_reload()
        active_cache = self.trackConfig.get_cache()
        active_model_view_array = active_cache.get_model_view_array()
        self.durationRecords = []
        self.durationObjects = []

        # durationRecords should be of type: FilesystemLabjackEvent_Record
        for aContainerObj in active_model_view_array:
            self.durationRecords.append(aContainerObj.get_record())
            newAnnotationIndex = len(self.durationObjects)
            newAnnotationView = aContainerObj.get_view()
            newAnnotationView.setAccessibleName(str(newAnnotationIndex))
            self.durationObjects.append(newAnnotationView)

        self.update_child_graph_widget()
        self.update()
        

    def build_child_graph_widget(self):
        self.graphWidget = pg.PlotWidget()
        self.layout().addWidget(self.graphWidget)

        # Configure the plot:

        # Add the Date-time axis
        axis = DateAxisItem(orientation='bottom')
        axis.attachToPlotItem(self.graphWidget.getPlotItem())

        #Add Background colour to white
        self.graphWidget.setBackground('w')

        #Add Axis Labels
        self.graphWidget.setLabel('left', 'Temperature (°C)', color='red', size=30)
        # self.graphWidget.setLabel('bottom', 'Hour (H)', color='red', size=30)
        
        #Add legend
        self.graphWidget.addLegend()

        self.graphWidget.showGrid(x=True, y=True)

        # self.graphWidget.setXRange(5, 20, padding=0)
        # self.graphWidget.setYRange(30, 40, padding=0)


    def plot(self, x, y, plotname, color):
        pen = pg.mkPen(color=color)
        self.graphWidget.plot(x, y, name=plotname, pen=pen, symbol='+', symbolSize=30, symbolBrush=(color))


    @pyqtSlot()
    def update_child_graph_widget(self):
        
        # hour = [1,2,3,4,5,6,7,8,9,10]
        # x_vals = hour

        out_data_series = dict()

        all_variable_timestamps = []
        for aDurationRecord in self.durationRecords:
            # Add x-value
            # curr_x_val = aDurationRecord.start_date
            curr_x_val = time.mktime(aDurationRecord.start_date.timetuple())

            all_variable_timestamps.append(curr_x_val)
            curr_var_name = aDurationRecord.variable_name
            curr_var_color = aDurationRecord.variable_color
            # curr_extended_info_dict = aDurationRecord.extended_info_dict
            
            if curr_var_name not in out_data_series.keys():
                # create a new series if needed
                out_data_series[curr_var_name] = {'x': list(), 'y':list(), 'color':curr_var_color, 'name': curr_var_name}

            out_data_series[curr_var_name]['x'].append(curr_x_val)
            out_data_series[curr_var_name]['y'].append(1.0)


        if len(out_data_series) > 0:
            # Build the plots:
            print('out_data_series contains {} items...'.format(len(out_data_series)))
            for (aVariableName, aDictValue) in out_data_series.items():
                # plot data: x, y values
                self.plot(aDictValue['x'], aDictValue['y'], aDictValue['name'], aDictValue['color'])
                
        else:
            print('WARNING: out_data_series is empty!')
            # plot some random data with timestamps in the last hour
            # # now = time.time()
            # # timestamps = numpy.linspace(now - 3600, now, 100)


            # # Looks like we want relative timestamp offsets.
            # # self.totalStartTime = totalStartTime
            # # self.totalEndTime = totalEndTime
            # # self.totalDuration = (self.totalEndTime - self.totalStartTime)
            # # self.fixedWidth = 800.0

            # # Draw the instantaneous event objects
            # # for (index, obj) in enumerate(self.instantaneousObjects):
            # #     self.instantaneousEventRect[index] = obj.paint(qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)
            # # self.offset_to_datetime()
            # x_vals = timestamps


            # temperature_1 = [30,32,34,32,33,31,29,32,35,45]
            # temperature_2 = [50,35,44,22,38,32,27,38,32,44]

            # # plot data: x, y values
            # self.plot(x_vals, temperature_1, "Sensor1", 'r')
            # self.plot(x_vals, temperature_2, "Sensor2", 'b')

            # self.graphWidget.plot(hour, temperature)
            
            self.graphWidget.clear()

            pass











    # overrides
    def reset_hovered(self):
        super().reset_hovered()


    def reset_selected(self):
        super().reset_selected()


    def paintEvent( self, event ):
        qp = QtGui.QPainter()
        qp.begin( self )
        # TODO: minor speedup by re-using the array of QRect objects if the size doesn't change
        self.eventRect = np.repeat(QRect(0,0,0,0), len(self.durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0, 0, 0, 0), len(self.instantaneousObjects))

        ## TODO: Use viewport information to only draw the currently displayed rectangles instead of having to draw it all at once.
        drawRect = self.rect()

        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            self.eventRect[index] = obj.paint( qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)
            
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            self.instantaneousEventRect[index] = obj.paint(qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)

        qp.end()

    def set_active_filter(self, start_datetime, end_datetime):
        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        self.update()


    def on_button_clicked(self, event):
        super().on_button_clicked(event)

    def on_button_released(self, event):
        super().on_button_released(event)
                
    def on_key_pressed(self, event):
        super().on_key_pressed(event)

    def on_key_released(self, event):
        super().on_key_released(event)

    def on_mouse_moved(self, event):
        super().on_mouse_moved(event)

