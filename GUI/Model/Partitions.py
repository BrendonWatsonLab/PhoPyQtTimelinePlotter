import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.Model.Events.PhoEvent import PhoEvent
from GUI.Model.Events.PhoDurationEvent import PhoDurationEvent
from GUI.Model.Events.PhoDurationEvent_Partition import PhoDurationEvent_Partition

# from app.BehaviorsList import BehaviorsManager

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingQObject

from app.database.entry_models.db_model import CategoricalDurationLabel, Context, Subcontext
# """
# Represents a partition
# """
# class PartitionInfo(QObject):
#     def __init__(self, name='', start_pos=0.0, end_pos=1.0, extended_data=dict()):
#         super(PartitionInfo, self).__init__(None)
#         self.name = name
#         self.start_pos = start_pos
#         self.end_pos = end_pos
#         self.extended_data = extended_data

#     def __eq__(self, otherEvent):
#         return self.name == otherEvent.name and self.start_pos == otherEvent.start_pos and self.end_pos == otherEvent.end_pos

#     # Less Than (<) operator
#     def __lt__(self, otherEvent):
#         return self.start_pos < otherEvent.start_pos

#     def __str__(self):
#         return 'Event {0}: start_pos: {1}, end_pos: {2}, extended_data: {3}'.format(self.name, self.start_pos, self.end_pos, str(self.extended_data))

"""
A 0.0 to 1.0 timeline
"""
class Partitioner(AbstractDatabaseAccessingQObject):
    # TODO: Could just use its owning_parent_track's database_connection?
    def __init__(self, totalStartTime, totalEndTime, owning_parent_track, database_connection, name='', partitions=None, partitionDataObjects=None, extended_data=dict()):
        super(Partitioner, self).__init__(database_connection)
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)
        self.owning_parent_track = owning_parent_track
        self.name = name
        # self.behaviorsManager = BehaviorsManager()
        needs_initialize_partitions = False
        if (not (partitions is None)):
            if (len(partitions) > 0):
                self.partitions = partitions
                needs_initialize_partitions = False
            else:
                needs_initialize_partitions = True
        else:
            if (partitionDataObjects is not None):
                self.rebuild_gui_partitions(partitionDataObjects)
                needs_initialize_partitions = (len(self.partitions) <= 0)
            else:
                needs_initialize_partitions = True


        if needs_initialize_partitions:
            new_partition_obj = PhoDurationEvent_Partition(self.totalStartTime, self.totalEndTime, '0', parent=self.owning_parent_track)
            new_partition_obj.on_edit.connect(self.owning_parent_track.on_partition_modify_event)
            self.partitions = [new_partition_obj] # Create default partition
    
        self.extended_data = extended_data

    def __eq__(self, otherEvent):
        return self.name == otherEvent.name and self.totalDuration == otherEvent.totalDuration

    # Less Than (<) operator
    def __lt__(self, otherEvent):
        return self.startTime < otherEvent.startTime

    def __str__(self):
        return 'Event {0}: startTime: {1}, partitions: {2}, extended_data: {3}'.format(self.name, self.partitions, self.color, str(self.extended_data))

    def cut_partition(self, cut_partition_index, cut_datetime):
        # Creates a cut at a given datetime
        partition_to_cut = self.partitions[cut_partition_index]
        if (partition_to_cut.startTime < cut_datetime < partition_to_cut.endTime):
            # only can cut if it's in the appropriate partition.
            # Create a new partition and insert it after the partition to cut. It should span from [cut_datetime, to the end of the cut partition]
            new_partition_index = cut_partition_index+1
            new_partition_obj = PhoDurationEvent_Partition(cut_datetime, partition_to_cut.endTime, str(new_partition_index), parent=self.owning_parent_track)
            new_partition_obj.on_edit.connect(self.owning_parent_track.on_partition_modify_event)

            self.partitions.insert(new_partition_index, new_partition_obj)
            self.partitions[cut_partition_index].endTime = cut_datetime # Truncate the partition to cut to the cut_datetime
            return True
        else:
            print('Error! Tried to cut invalid partition! parition[{0}]: (start: {1}, attemptted_cut: {2}, end: {3})'.format(cut_partition_index, partition_to_cut.startTime, cut_datetime, partition_to_cut.endTime))
            return False

        # The first partition keeps the metadata/info, while the second is initialized to a blank partition

    # Called when the Partition Edit Dialog returns with an accept message. Called from TimelineTrackDrawingWidget_Partition's try_update_partition(...) function
    def modify_partition(self, modify_partition_index, start_date, end_date, title, subtitle, body, type_id, subtype_id, color):
        partition_to_modify = self.partitions[modify_partition_index]
        if (not partition_to_modify):
            print('invalid partition to modify!')
            return
        if (not (partition_to_modify.startTime == start_date)):
            # Start time changed
            if (modify_partition_index > 0):
                # Get the preceding partition, as it will need to be changed too
                prec_partition_index = modify_partition_index-1
                prec_partition = self.partitions[prec_partition_index]
                # TODO: Update its end time
                prec_partition.endTime = start_date
                prec_partition.totalDuration = (prec_partition.endTime - prec_partition.startTime)
                self.partitions[prec_partition_index] = prec_partition

            partition_to_modify.startTime = start_date
        
        if (not (partition_to_modify.endTime == end_date)):
            # End time changed
            if (modify_partition_index < (len(self.partitions)-1)):
                # Get the following partition, as it will need to be changed too
                foll_partition_index = modify_partition_index+1
                foll_partition = self.partitions[foll_partition_index]
                foll_partition.startTime = end_date
                foll_partition.totalDuration = (foll_partition.endTime - foll_partition.startTime)
                self.partitions[foll_partition_index] = foll_partition
                # TODO: Update its end time

            partition_to_modify.endTime = end_date

        partition_to_modify.totalDuration = (partition_to_modify.endTime - partition_to_modify.startTime)

        # Rename it if needed
        if (not (partition_to_modify.name == title)):
            partition_to_modify.name = title

        partition_to_modify.subtitle = subtitle
        partition_to_modify.body = body

        if (not (partition_to_modify.type_id == type_id)):
            partition_to_modify.type_id = type_id
            

        if (not (partition_to_modify.subtype_id == subtype_id)):
            partition_to_modify.subtype_id = subtype_id
            # partition_to_modify.color = self.behaviorsManager.get_subtype_color(subtype_id)
            partition_to_modify.color = color
        

        # Update in the array
        self.partitions[modify_partition_index] = partition_to_modify

    @staticmethod
    def get_gui_partition(from_database_partition_record, parent):
        # Get new color associated with the modified subtype_id
        # TODO: maybe more dynamic getting of color from parent track?
        # theColor = parent.behaviors[from_database_partition_record.subtype_id-1].primaryColor.get_QColor()
        # Get new color associated with the modified subtype_id
        if ((from_database_partition_record.type_id is None) or (from_database_partition_record.subtype_id is None)):
            theColor = PhoDurationEvent_Partition.ColorBase
        else:
            theColor = parent.behaviors[from_database_partition_record.subtype_id-1].primaryColor.get_QColor()
        # theColor = Qt.black
        outPartitionGuiObj = PhoDurationEvent_Partition(from_database_partition_record.start_date, from_database_partition_record.end_date, \
            from_database_partition_record.primary_text, from_database_partition_record.secondary_text, from_database_partition_record.tertiary_text, \
                theColor, from_database_partition_record.type_id, from_database_partition_record.subtype_id, {'notes':from_database_partition_record.notes}, parent=parent)
        outPartitionGuiObj.on_edit.connect(parent.on_partition_modify_event)
        return outPartitionGuiObj

    def rebuild_gui_partitions(self, from_data_partitions):
        self.partitions = []
        for (anIndex, aDataObj) in enumerate(from_data_partitions):
            # Create the graphical annotation object
            newGuiObject = Partitioner.get_gui_partition(aDataObj, self.owning_parent_track)
            # newGuiObject.on_edit.connect(self.owning_parent_track.on_partition_modify_event)

            # Get new color associated with the modified subtype_id
            # TODO: maybe more dynamic getting of color from parent track?
            # theColor = self.owning_parent_track.behaviors[from_database_partition_record.subtype_id-1].primaryColor.get_QColor()

            newPartitionIndex = len(self.partitions)
            newGuiObject.setAccessibleName(str(newPartitionIndex))

            self.partitions.append(newGuiObject)



    def save_partitions_to_database(self, contextObj, subcontextObj):
        print("partitions manager: save_partitions_to_database({0}, {1})".format(str(contextObj), str(subcontextObj)))
        # newBehaviorContext = Context(None, "Behavior")
        # newBehaviorSubcontext = Subcontext(None, "Manual", newBehaviorContext)
        print("trying to save {0} partition objects".format(len(self.partitions)))

        # Tries to save the active partitions out to the database
        for (index, aPartitionObj) in enumerate(self.partitions):
            newPartRecord = CategoricalDurationLabel()
            newPartRecord.start_date = aPartitionObj.startTime
            newPartRecord.end_date = aPartitionObj.endTime
            
            newPartRecord.label_created_date = datetime.now()
            newPartRecord.label_created_user = "Unknown User"
            # Set the last updated properties to the creation properties (since we just created it)
            newPartRecord.last_updated_user = newPartRecord.label_created_user
            newPartRecord.last_updated_date = newPartRecord.label_created_date

            newPartRecord.Context = contextObj
            newPartRecord.Subcontext = subcontextObj

            newPartRecord.type_id = aPartitionObj.type_id
            newPartRecord.subtype_id = aPartitionObj.subtype_id
            newPartRecord.tertiarytype_id = None

            newPartRecord.primary_text = aPartitionObj.name
            newPartRecord.secondary_text = aPartitionObj.subtitle
            newPartRecord.tertiary_text = aPartitionObj.body

            newPartRecord.notes = 'auto'

            self.database_connection.save_to_database([newPartRecord], 'CategoricalDurationLabel')

        print("done.")
            

