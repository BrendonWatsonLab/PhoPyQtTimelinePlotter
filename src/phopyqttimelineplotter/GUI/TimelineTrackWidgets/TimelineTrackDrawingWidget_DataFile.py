# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
import time
from datetime import datetime, timedelta, timezone
from enum import Enum

import matplotlib
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# matplotlib.use("Qt5agg") # or "Qt5agg" depending on you version of Qt
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pandas.plotting import register_matplotlib_converters
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
)

register_matplotlib_converters()


import pyqtgraph as pg
from phopyqttimelineplotter.app.database.SqlAlchemyDatabase import (
    convert_TimestampedAnnotation,
    create_TimestampedAnnotation,
    modify_TimestampedAnnotation,
    modify_TimestampedAnnotation_endDate,
    modify_TimestampedAnnotation_startDate,
)
from lib.pg_time_axis import DateAxisItem

# from pyqtgraph import PlotWidget, plot, widgets
# from pyqtgraph.widgets import MatplotlibWidget
from pyqtgraph import PlotWidget, plot

# from pyqtgraph.widgets import pg.widgets.MatplotlibWidget
from pyqtgraph.widgets import MatplotlibWidget

from phopyqttimelineplotter.GUI.Model.Events.PhoDurationEvent_AnnotationComment import *
from phopyqttimelineplotter.GUI.Model.TrackType import (
    TrackConfigDataCacheMixin,
    TrackConfigMixin,
    TrackType,
)
from phopyqttimelineplotter.GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_SelectionBase import (
    TimelineTrackDrawingWidget_SelectionBase,
)
from phopyqttimelineplotter.GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import (
    ItemSelectionOptions,
    TimelineTrackDrawingWidgetBase,
)
from phopyqttimelineplotter.GUI.UI.TextAnnotations.TextAnnotationDialog import *

# from pyqtgraph.widgets import MatplotlibWidget


class DataTrackDisplayMode(Enum):
    standardEventDrawing = 0
    pyQtGraph = 1
    matplotlibGraph = 2

    def should_paint_events(self):
        return self == DataTrackDisplayMode.standardEventDrawing

    def should_build_event_views(self):
        return self == DataTrackDisplayMode.standardEventDrawing

    def should_use_child_graph(self):
        return (self is DataTrackDisplayMode.pyQtGraph) or (
            self is DataTrackDisplayMode.matplotlibGraph
        )


"""
    This track draws a data file (.csv labjack file, for example) as a series of events along the timeline.
"""


class TimelineTrackDrawingWidget_DataFile(
    TrackConfigDataCacheMixin,
    TrackConfigMixin,
    TimelineTrackDrawingWidget_SelectionBase,
):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.SingleSelection

    default_dataDisplayMode = DataTrackDisplayMode.pyQtGraph
    # default_dataDisplayMode = DataTrackDisplayMode.matplotlibGraph

    def __init__(
        self,
        trackConfig,
        totalStartTime,
        totalEndTime,
        database_connection,
        parent=None,
        wantsKeyboardEvents=False,
        wantsMouseEvents=True,
    ):
        self.trackConfig = trackConfig
        super(TimelineTrackDrawingWidget_DataFile, self).__init__(
            trackConfig.get_track_id(),
            totalStartTime,
            totalEndTime,
            [],
            database_connection=database_connection,
            parent=parent,
            wantsKeyboardEvents=wantsKeyboardEvents,
            wantsMouseEvents=wantsMouseEvents,
        )
        # self.durationObjects = durationObjects
        self.instantaneousObjects = []
        # self.eventRect = np.repeat(QRect(0,0,0,0), len(durationObjects))
        self.instantaneousEventRect = np.repeat(
            QRect(0, 0, 0, 0), len(self.instantaneousObjects)
        )

        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        self.hovered_duration_object_indicies = []

        # Selected Object
        self.selected_duration_object_indicies = []
        self.shouldDismissSelectionUponMouseButtonRelease = (
            TimelineTrackDrawingWidget_DataFile.default_shouldDismissSelectionUponMouseButtonRelease
        )
        self.itemSelectionMode = (
            TimelineTrackDrawingWidget_DataFile.default_itemSelectionMode
        )
        self.itemHoverMode = (
            TimelineTrackDrawingWidget_SelectionBase.default_itemHoverMode
        )

        # Setup Layout
        self.dataDisplayMode = (
            TimelineTrackDrawingWidget_DataFile.default_dataDisplayMode
        )
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
        # TODO: figure out how to pass file path
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
        if self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph:
            self.graphWidget = pg.PlotWidget()

        elif self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph:
            # self.graphWidget = widgets.MatplotlibWidget()
            # self.graphWidget = pg.widgets.MatplotlibWidget
            # self.graphWidget = MatplotlibWidget.MatplotlibWidget(size=(5.0, 4.0), dpi=120)
            self.graphWidget = MatplotlibWidget.MatplotlibWidget()

        else:
            print("ERROR: wrong mode!")
            return

        self.layout().addWidget(self.graphWidget)
        # self.graphWidget.setMinimumSize(self.minimumWidth, self.minimumHeight)
        self.graphWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        # self.graphWidget.size

        # Configure the plot:
        if self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph:

            # Add the Date-time axis
            axis = DateAxisItem(orientation="bottom")
            axis.attachToPlotItem(self.graphWidget.getPlotItem())

            # Add Background colour to white
            clear_color = pg.mkColor(0, 0, 0, 0)
            self.graphWidget.setBackground(clear_color)

            # Add Axis Labels
            self.graphWidget.setLabel("left", "Temperature (°C)", color="red", size=30)
            # self.graphWidget.setLabel('bottom', 'Hour (H)', color='red', size=30)

            # Add legend
            self.graphWidget.addLegend()

            self.graphWidget.showGrid(x=True, y=True)

            curr_global_min_x_val = time.mktime(self.totalStartTime.timetuple())
            curr_global_max_x_val = time.mktime(self.totalEndTime.timetuple())

            self.graphWidget.setXRange(
                curr_global_min_x_val, curr_global_max_x_val, padding=0
            )
            self.graphWidget.setYRange(0, 1.1, padding=0)

        elif self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph:
            # TODO: configure the matplotlib plot:
            fig = self.graphWidget.getFigure()

            fig.suptitle("Labjack Data")

            # fig.set_facecolor(1,1,1)
            fig.patch.set_facecolor((0.1, 0.2, 0.5, 0.3))

            # fig.set_y
            # Draw the widget:
            self.graphWidget.draw()

            pass

    def plot(self, x, y, plotname, color):
        if self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph:
            pen = pg.mkPen(color=color)
            self.graphWidget.plot(
                x,
                y,
                name=plotname,
                pen=pen,
                symbol="+",
                symbolSize=30,
                symbolBrush=(color),
            )
            pass

        elif self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph:
            subplot = self.graphWidget.getFigure().add_subplot(111)
            subplot.plot(x, y)
            self.graphWidget.draw()
            pass

        else:
            print("ERROR: wrong mode!")
            return

    @pyqtSlot()
    def update_child_graph_widget(self):
        out_data_series = dict()
        out_variable_names = list()

        all_variable_timestamps = []
        for aDurationRecord in self.durationRecords:
            # Add x-value
            curr_x_val = None
            if self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph:
                curr_x_val = time.mktime(aDurationRecord.start_date.timetuple())
                pass
            elif self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph:
                curr_x_val = aDurationRecord.start_date
                pass

            all_variable_timestamps.append(curr_x_val)
            curr_var_name = aDurationRecord.variable_name
            curr_var_color = aDurationRecord.variable_color
            # curr_extended_info_dict = aDurationRecord.extended_info_dict

            if curr_var_name not in out_data_series.keys():
                # create a new series if needed
                out_variable_names.append(curr_var_name)
                out_data_series[curr_var_name] = {
                    "x": list(),
                    "y": list(),
                    "color": curr_var_color,
                    "name": curr_var_name,
                }

            out_data_series[curr_var_name]["x"].append(curr_x_val)
            out_data_series[curr_var_name]["y"].append(1.0)

        numVariables = len(out_variable_names)
        if numVariables > 0:
            # Build the plots:
            print("out_data_series contains {} items...".format(numVariables))

            if self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph:
                for (aVariableName, aDictValue) in out_data_series.items():
                    # plot data: x, y values
                    self.plot(
                        aDictValue["x"],
                        aDictValue["y"],
                        aDictValue["name"],
                        aDictValue["color"],
                    )

                pass

            elif self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph:
                # Create figure and plot a stem plot with the date
                # labjackDataLabels = out_data_series.items()

                # fig, axarr = plt.subplots(numVariables+1, sharex=True, sharey=True)
                # subplot = self.graphWidget.getFigure().add_subplot(111)

                fig = self.graphWidget.getFigure()
                # fig.set_facecolor(1,1,1)
                # fig.patch.set_facecolor(0.1, 0.2, 0.5, 0.3)

                axarr = fig.subplots(
                    numVariables + 1,
                    sharex=True,
                    sharey=True,
                )

                out_draw_objs_list = list()
                # out_draw_objs = {'markerline': None, 'stemline': None, 'baseline': None}
                # out_draw_objs = {'markerline': None, 'stemline': None, 'baseline': None}

                for variableIndex in range(0, numVariables):
                    aVariableName = out_variable_names[variableIndex]
                    aDictValue = out_data_series[aVariableName]
                    currAx = axarr[variableIndex]
                    curr_timestamps = aDictValue["x"]
                    curr_values = aDictValue["y"]
                    # plot data: x, y values
                    # self.plot(aDictValue['x'], aDictValue['y'], aDictValue['name'], aDictValue['color'])
                    markerline, stemline, baseline = currAx.stem(
                        curr_timestamps, curr_values, use_line_collection=True
                    )
                    out_draw_objs_list.append(
                        {
                            "markerline": markerline,
                            "stemline": stemline,
                            "baseline": baseline,
                        }
                    )

                    currAx.set_ylim(0.0, 1.1)
                    currAx.set_title("test {}".format(aVariableName))
                    # currAx.set_xticks(numpy.arange(0, 1, 0.1))
                    # currAx.set_yticks(numpy.arange(0, 1., 0.1))
                    # plt.grid(True)
                    # currAx.set_text
                    # plt.show()
                    self.graphWidget.draw()
                    # plt.show()

                # Bring subplots close to each other.
                fig.subplots_adjust(hspace=0)
                # Hide x labels and tick labels for all but bottom plot.
                for ax in axarr:
                    ax.label_outer()

                # Draw the widget:
                self.graphWidget.draw()

                pass

        else:
            print("WARNING: out_data_series is empty!")
            if self.dataDisplayMode is DataTrackDisplayMode.pyQtGraph:
                self.graphWidget.clear()
                pass
            elif self.dataDisplayMode is DataTrackDisplayMode.matplotlibGraph:
                # self.graphWidget.getFigure().clear()
                pass

            pass

    # overrides
    def reset_hovered(self):
        super().reset_hovered()

    def reset_selected(self):
        super().reset_selected()

    def paintEvent(self, event):

        if self.dataDisplayMode.should_paint_events():
            qp = QtGui.QPainter()
            qp.begin(self)
            # TODO: minor speedup by re-using the array of QRect objects if the size doesn't change
            self.eventRect = np.repeat(QRect(0, 0, 0, 0), len(self.durationObjects))
            self.instantaneousEventRect = np.repeat(
                QRect(0, 0, 0, 0), len(self.instantaneousObjects)
            )

            ## TODO: Use viewport information to only draw the currently displayed rectangles instead of having to draw it all at once.
            drawRect = self.rect()

            # Draw the duration objects
            for (index, obj) in enumerate(self.durationObjects):
                self.eventRect[index] = obj.paint(
                    qp,
                    self.totalStartTime,
                    self.totalEndTime,
                    self.totalDuration,
                    drawRect,
                )

            # Draw the instantaneous event objects
            for (index, obj) in enumerate(self.instantaneousObjects):
                self.instantaneousEventRect[index] = obj.paint(
                    qp,
                    self.totalStartTime,
                    self.totalEndTime,
                    self.totalDuration,
                    drawRect,
                )

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

    @staticmethod
    def plot_labjackData_Timeline(datetimes, labjackData, labjackDataLabels):
        # Create figure and plot a stem plot with the date
        numVariables = len(labjackDataLabels)
        numSamples = len(datetimes)
        print("numVariables: ", numVariables, " numSamples: ", numSamples)
        fig, axarr = plt.subplots(numVariables + 1, sharex=True, sharey=True)
        fig.suptitle("Labjack Data")

        for variableIndex in range(0, numVariables):
            currValues = labjackData[:, variableIndex]
            nonZeroEntries = np.nonzero(currValues)
            activeValues = currValues[nonZeroEntries]
            activeTimestamps = datetimes[nonZeroEntries]

            # markerline, stemline, baseline = axarr[variableIndex].stem(datetimes, labjackData[:, variableIndex], linefmt="C3-", basefmt="k-", use_line_collection=True)

            markerline, stemline, baseline = axarr[variableIndex].stem(
                activeTimestamps, activeValues, use_line_collection=True
            )
            # plt.setp(markerline, mec="k", mfc="w", zorder=3)

            # Shift the markers to the baseline by replacing the y-data by zeros.
            # markerline.set_ydata(np.zeros(numSamples))

        # Bring subplots close to each other.
        fig.subplots_adjust(hspace=0)
        # Hide x labels and tick labels for all but bottom plot.
        for ax in axarr:
            ax.label_outer()

        return (fig, axarr)

    @staticmethod
    def plot_combined_timeline(
        eventDatetimes,
        eventValues,
        eventLabels,
        videoStartTimes,
        videoEndTimes,
        videoLabels,
    ):
        def enter_axes(event):
            # print('enter_axes', event.inaxes)
            event.inaxes.patch.set_facecolor("wheat")
            event.canvas.draw()

        def leave_axes(event):
            # print('leave_axes', event.inaxes)
            event.inaxes.patch.set_facecolor("white")
            event.canvas.draw()

        def enter_figure(event):
            # print('enter_figure', event.canvas.figure)
            event.canvas.figure.patch.set_facecolor("salmon")
            event.canvas.draw()

        def leave_figure(event):
            # print('leave_figure', event.canvas.figure)
            event.canvas.figure.patch.set_facecolor("grey")
            event.canvas.draw()

        # def onpick(event):
        #     thisline = event.artist
        #     xdata = thisline.get_xdata()
        #     ydata = thisline.get_ydata()
        #     ind = event.ind
        #     points = tuple(zip(xdata[ind], ydata[ind]))
        #     print('onpick points:', points)

        # Create figure and plot a stem plot with the date
        numVariables = len(eventLabels)
        numSamples = len(eventDatetimes)
        # numSubplots = numVariables + 1
        numSubplots = int((numVariables / 2) + 1)
        # print('numVariables: ', numVariables, " numSamples: ", numSamples)
        fig, axarr = plt.subplots(numSubplots, sharex=True, sharey=True)
        fig.suptitle("Combined Data")

        # ax_colors = ['aqua','blue','aquamarine','darkblue','coral','crimson','magenta','maroon']
        ax_colors = [
            "aqua",
            "aquamarine",
            "coral",
            "magenta",
            "blue",
            "darkblue",
            "crimson",
            "maroon",
        ]

        ## Iterate through the event variables and plot them on the appropriate subplots
        for variableIndex in range(0, numVariables):
            currValues = eventValues[:, variableIndex]
            nonZeroEntries = np.nonzero(currValues)
            activeValues = currValues[nonZeroEntries]
            activeTimestamps = eventDatetimes[nonZeroEntries]

            # markerline, stemline, baseline = axarr[variableIndex].stem(datetimes, labjackData[:, variableIndex], linefmt="C3-", basefmt="k-", use_line_collection=True)
            # markerline, stemline, baseline = axarr[variableIndex].stem(activeTimestamps, activeValues, use_line_collection=True)
            # Make taller for dispense events
            activeOffset = 0
            activeLineLength = 1
            if variableIndex > 3:
                activeValues = activeValues * 2
                activeOffset = 1
                activeLineLength = 3

            # markerline, stemline, baseline = axarr[(variableIndex % 4)].stem(activeTimestamps, activeValues, use_line_collection=True, picker=5)
            # #axarr[variableIndex].set(title=eventLabels[variableIndex])
            # #plt.setp(markerline, mec="k", mfc="w", zorder=3)
            # # Shift the markers to the baseline by replacing the y-data by zeros.
            # markerline.set_ydata(np.zeros_like(activeValues))
            #

            # print('timestamps:', len(activeTimestamps), "  values: ", len(activeValues))
            # axarr[(variableIndex % 4)].eventplot(activeTimestamps, orientation='horizontal', linelengths=activeValues)
            # axarr[(variableIndex % 4)].eventplot(activeTimestamps, orientation='horizontal', linewidths=activeValues)
            axarr[(variableIndex % 4)].eventplot(
                activeTimestamps,
                orientation="horizontal",
                lineoffsets=activeOffset,
                linelengths=activeLineLength,
                color=ax_colors[variableIndex],
                picker=5,
            )

            axarr[(variableIndex % 4)].get_yaxis().set_visible(False)
            for spine in ["left", "top", "right"]:
                axarr[(variableIndex % 4)].spines[spine].set_visible(False)

        ## Plot the video variables
        videoAx = axarr[-1]
        # videoAx.set(title="Timeline HLines")
        colors = np.tile(
            ["red", "green", "blue", "yellow"], int(np.ceil(len(videoStartTimes) / 4))
        )[: len(videoStartTimes)]
        videoAx.grid(True)
        # Format X-Axis:
        myFmt = mdates.DateFormatter("%m-%d")
        videoAx.xaxis.set_major_formatter(myFmt)

        # Format Y-Axis:
        # ax.set_yticklabels([])
        # ax.set_yticks([])
        # remove y axis and spines
        videoAx.get_yaxis().set_visible(False)
        for spine in ["left", "top", "right"]:
            videoAx.spines[spine].set_visible(False)
        videoAx.get_yaxis().grid(b=None)

        # Interactivity:
        annot = videoAx.annotate(
            "",
            xy=(0, 0),
            xytext=(-20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="white", ec="b", lw=2),
            arrowprops=dict(arrowstyle="->"),
        )
        annot.set_visible(False)
        hlines_objs = []
        for i in range(0, (len(videoStartTimes) - 1)):
            # color = random.choice(['red', 'green', 'blue', 'yellow'])
            currStartDate = videoStartTimes[i]
            currEndDate = videoEndTimes[i]
            currLabel = videoLabels[i]
            hlines_objs.append(
                plt.hlines(
                    1,
                    currStartDate,
                    currEndDate,
                    colors=colors[i],
                    lw=20,
                    label=currLabel,
                )
            )
            plt.text(
                currStartDate, 1.01, currLabel, horizontalalignment="left", rotation=45
            )

        def update_annot_line(event, line, line_index, contained_object_index):
            # Find which box or line we have clicked on
            index = contained_object_index[0]
            # Find the vertices of the object
            verts = line.get_paths()[index].vertices
            # Print the minimum and maximum extent of the object in x and y
            # print("X = {}, {}".format(verts[:, 0].min(), verts[:, 0].max()))
            # print("Y = {}, {}".format(verts[:, 1].min(), verts[:, 1].max()))
            annot.xy = (verts[index, 0], verts[index, 1])
            # Get the position from the event object
            xOffset = event.xdata
            # print(xOffset)
            xDate = mdates.num2date(xOffset)
            # print(xDate)
            xDateString = xDate.strftime("%m-%d %I:%M:%S.%f %p")
            # print(xDateString)
            # xLimDateNums = event.inaxes.get_xlim()
            # xLimRange = xLimDateNums[1] - xLimDateNums[0]

            # Format the text to display on the annotation
            text = "{}, {}\n{}".format(
                " ".join(list(map(str, contained_object_index))),
                " ".join([videoLabels[line_index]]),
                " ".join([xDateString]),
            )
            # " ".join([np.format_float_positional(xOffset)]))
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.6)

        def hover_line(event):
            is_annot_visible = annot.get_visible()
            # Only do this for the video axes
            if event.inaxes == videoAx:
                # Enumerate each video block
                for lineIndex, lineObj in enumerate(hlines_objs):
                    # Check if the event fell within the line object
                    does_contain_event, ind = lineObj.contains(event)
                    if does_contain_event:
                        update_annot_line(event, lineObj, lineIndex, ind["ind"])
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return

            if is_annot_visible:
                annot.set_visible(False)
                fig.canvas.draw_idle()

        def video_relative_timestamp(aTimestamp):
            aDatetimeTimestamp = mdates.num2date(aTimestamp).replace(tzinfo=None)
            foundVideoIndex = None
            foundVideoRelativeTimestamp = None
            for (videoIndex, videoStartDate) in enumerate(videoStartTimes):
                videoEndDate = videoEndTimes[videoIndex]
                if videoStartDate <= aDatetimeTimestamp <= videoEndDate:
                    foundVideoIndex = videoIndex
                    foundVideoRelativeTimestamp = aDatetimeTimestamp - videoStartDate
                    return (foundVideoIndex, foundVideoRelativeTimestamp)

            return (foundVideoIndex, foundVideoRelativeTimestamp)

        def onpick(event):
            thisEventCollection = event.artist

            print(str(event))
            print(str(thisEventCollection))
            # Find the vertices of the object
            verts = thisEventCollection.get_paths()[0].vertices
            print(str(verts))

            xVal = verts[0, 0]
            (foundVideoIndex, foundVideoRelativeTimestamp) = video_relative_timestamp(
                xVal
            )
            if foundVideoRelativeTimestamp:
                print(foundVideoRelativeTimestamp)
                return
            else:
                print("No video.")
                return

            # for (anEventObjIndex, anEventObj) in enumerate(thisEventCollection):
            #     # Check if the event fell within the line object
            #     does_contain_event, ind = anEventObj.contains(event)
            #     if does_contain_event:
            #         print('Contains: ', ind["ind"])
            #         # ind["ind"]
            #         # update_annot_line(event, lineObj, lineIndex, ind["ind"])
            #         # annot.set_visible(True)
            #         # fig.canvas.draw_idle()
            #         return

            # # Check if the event fell within the line object
            # does_contain_event, ind = thisEventCollection.contains(event)
            # if does_contain_event:
            #     print('Contains: ', ind["ind"])
            #     # ind["ind"]
            #     # update_annot_line(event, lineObj, lineIndex, ind["ind"])
            #     # annot.set_visible(True)
            #     # fig.canvas.draw_idle()
            #     return

            # xdata = thisline.get_xdata()
            # ydata = thisline.get_ydata()
            # ind = event.ind
            # points = tuple(zip(xdata[ind], ydata[ind]))
            # print('onpick points:', points)

        fig.canvas.mpl_connect("motion_notify_event", hover_line)
        fig.canvas.mpl_connect("figure_enter_event", enter_figure)
        fig.canvas.mpl_connect("figure_leave_event", leave_figure)
        fig.canvas.mpl_connect("axes_enter_event", enter_axes)
        fig.canvas.mpl_connect("axes_leave_event", leave_axes)
        fig.canvas.mpl_connect("pick_event", onpick)

        # Bring subplots close to each other.
        fig.subplots_adjust(hspace=0)
        # Hide x labels and tick labels for all but bottom plot.
        for ax in axarr:
            ax.label_outer()

        plt.show()
