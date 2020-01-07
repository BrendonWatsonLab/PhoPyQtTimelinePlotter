# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from enum import Enum

import time
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

# from pyqtgraph import PlotWidget, plot, widgets
# from pyqtgraph.widgets import MatplotlibWidget
from pyqtgraph import PlotWidget, plot
# from pyqtgraph.widgets import MatplotlibWidget

# from pyqtgraph.widgets import pg.widgets.MatplotlibWidget
from pyqtgraph.widgets import MatplotlibWidget

import pyqtgraph as pg
from lib.pg_time_axis import DateAxisItem


import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors


from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import TimelineTrackDrawingWidgetBase, ItemSelectionOptions
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_SelectionBase import TimelineTrackDrawingWidget_SelectionBase

from GUI.Model.Events.PhoDurationEvent_AnnotationComment import *
from GUI.UI.TextAnnotations.TextAnnotationDialog import *

from app.database.SqlAlchemyDatabase import create_TimestampedAnnotation, convert_TimestampedAnnotation, modify_TimestampedAnnotation, modify_TimestampedAnnotation_startDate, modify_TimestampedAnnotation_endDate

from GUI.Model.TrackType import TrackType, TrackConfigMixin, TrackConfigDataCacheMixin


class DataTrackDisplayMode(Enum):
    standardEventDrawing = 0
    pyQtGraph = 1
    matplotlibGraph = 2

    def should_paint_events(self):
        return (self == DataTrackDisplayMode.standardEventDrawing)

    def should_build_event_views(self):
        return (self == DataTrackDisplayMode.standardEventDrawing)

    def should_use_child_graph(self):
        return ((self is DataTrackDisplayMode.pyQtGraph) or (self is DataTrackDisplayMode.matplotlibGraph))



"""
    This track draws a data file (.csv labjack file, for example) as a series of events along the timeline.
"""
class TimelineTrackDrawingWidget_DataFile(TrackConfigDataCacheMixin, TrackConfigMixin, TimelineTrackDrawingWidget_SelectionBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.SingleSelection

    # default_dataDisplayMode = DataTrackDisplayMode.pyQtGraph
    default_dataDisplayMode = DataTrackDisplayMode.matplotlibGraph

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
        self.dataDisplayMode = TimelineTrackDrawingWidget_DataFile.default_dataDisplayMode
        if self.dataDisplayMode.should_use_child_graph():
            self.setLayout(QVBoxLayout())
            self.build_child_graph_widget()

        self.setMouseTracking(True)

        self.trackConfig.cacheUpdated.connect(self.on_reloadModelFromConfigCache)
        self.reloadModelFromDatabase()

        if self.dataDisplayMode.should_use_child_graph():
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

            # Note: self.durationObjects is empty if we aren't in standardEventDrawing dataDisplayMode
            if self.dataDisplayMode.should_build_event_views():
                newAnnotationIndex = len(self.durationObjects)
                newAnnotationView = aContainerObj.get_view()
                newAnnotationView.setAccessibleName(str(newAnnotationIndex))
                self.durationObjects.append(newAnnotationView)


        if self.dataDisplayMode.should_use_child_graph():
            self.update_child_graph_widget()
    
        self.update()
        

    def build_child_graph_widget(self):
        self.graphWidget = None
        if (self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph):
            self.graphWidget = pg.PlotWidget()
            
        elif (self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph):
            # self.graphWidget = widgets.MatplotlibWidget()
            # self.graphWidget = pg.widgets.MatplotlibWidget
            self.graphWidget = MatplotlibWidget.MatplotlibWidget(size=(5.0, 4.0), dpi=120)


        else:
            print("ERROR: wrong mode!")
            return
        
        self.layout().addWidget(self.graphWidget)

        # Configure the plot:
        if (self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph):

            # Add the Date-time axis
            axis = DateAxisItem(orientation='bottom')
            axis.attachToPlotItem(self.graphWidget.getPlotItem())

            #Add Background colour to white
            clear_color = pg.mkColor(0, 0, 0, 0)
            self.graphWidget.setBackground(clear_color)

            #Add Axis Labels
            self.graphWidget.setLabel('left', 'Temperature (°C)', color='red', size=30)
            # self.graphWidget.setLabel('bottom', 'Hour (H)', color='red', size=30)
            
            #Add legend
            self.graphWidget.addLegend()

            self.graphWidget.showGrid(x=True, y=True)

            curr_global_min_x_val = time.mktime(self.totalStartTime.timetuple())
            curr_global_max_x_val = time.mktime(self.totalEndTime.timetuple())

            self.graphWidget.setXRange(curr_global_min_x_val, curr_global_max_x_val, padding=0)
            self.graphWidget.setYRange(0, 1.1, padding=0)
            

            
        elif (self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph):
            # TODO: configure the matplotlib plot:

            pass


        


    def plot(self, x, y, plotname, color):
        if (self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph):
            pen = pg.mkPen(color=color)
            self.graphWidget.plot(x, y, name=plotname, pen=pen, symbol='+', symbolSize=30, symbolBrush=(color))
            pass

        elif (self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph):
            subplot = self.graphWidget.getFigure().add_subplot(111)
            subplot.plot(x,y)
            self.graphWidget.draw()
            pass

        else:
            print("ERROR: wrong mode!")
            return





    @pyqtSlot()
    def update_child_graph_widget(self):
        out_data_series = dict()

        all_variable_timestamps = []
        for aDurationRecord in self.durationRecords:
            # Add x-value
            curr_x_val = None
            if (self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph):
                curr_x_val = time.mktime(aDurationRecord.start_date.timetuple())
                pass
            elif (self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph):
                curr_x_val = aDurationRecord.start_date
                pass


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

            
            if (self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph):
                self.graphWidget.clear()
                pass
            elif (self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph):
                self.graphWidget.getFigure().clear()
                pass


            pass



    # overrides
    def reset_hovered(self):
        super().reset_hovered()


    def reset_selected(self):
        super().reset_selected()


    def paintEvent( self, event ):

        if self.dataDisplayMode.should_paint_events():
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


        # Note: An efficient pyqtgraph function that returns a QPainterPath from pairs of points that should be connected in the most efficient way possible. This seems like a good way to draw spikes.
        # qpPath = pg.arrayToQPath(x, y, connect='pairs')




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

