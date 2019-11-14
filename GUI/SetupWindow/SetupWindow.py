# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timezone, timedelta
# import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog, QTreeWidget, QTreeWidgetItem
# from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.UI.AbstractDatabaseAccessingWindow import AbstractDatabaseAccessingWindow

from app.BehaviorsList import BehaviorsManager, BehaviorInfoOptions
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors

# from GUI.UI.EditCapableTableView import EditCapableTableView

class SetupWindow(AbstractDatabaseAccessingWindow):
    def __init__(self, database_connection):
        super(SetupWindow, self).__init__(database_connection) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/SetupWindow/SetupWindow.ui", self) # Load the .ui file
        self.behaviorsManager = BehaviorsManager()

        # The most recently selected/activated table cell index (column, row) or None
        self.behaviorsTableActiveIndex = None

        # The table index currently being edited
        self.behaviorsTableEditingIndex = None

        self.initUI()

    def initUI(self):
        
        # self.ui.tableWidget_Settings_PartitionTrack.setH

        # if you don't want to allow in-table editing, either disable the table like:
        # self.ui.tableWidget_Settings_PartitionTrack.setEditTriggers(QTableWidget.NoEditTriggers)

        # or specifically for this item
        # self.ui.tableWidget_Settings_PartitionTrack.setFlags(item.flags() ^ Qt.ItemIsEditable)

        # create a connection to the double click event
        self.ui.tableWidget_Settings_PartitionTrack.itemDoubleClicked.connect(self.editItem)

        # Not sure which function I want to use
        self.ui.tableWidget_Settings_PartitionTrack.itemChanged.connect(self.on_item_changed)
        self.ui.tableWidget_Settings_PartitionTrack.currentItemChanged.connect(self.on_current_item_changed)

        self.initBehaviorsInterfaces()


    # Creates both the behavior tree and the behaviors database from a set of hard-coded values defined in behaviorsManager
    def initSampleBehaviorsDatabase(self):
        self.topLevelNodes = []
        self.topLeftNodesDict = dict()

        # Create new colors if needed
        default_black_color_hex = QColor(0,0,0).name(QColor.HexRgb)
        default_black_color = CategoryColors(None, default_black_color_hex, 'Black', 'Black', 0, 0, 0, None)
        default_white_color_hex = QColor(255,255,255).name(QColor.HexRgb)
        default_white_color = CategoryColors(None, default_white_color_hex,'White', 'White', 255, 255, 255, None)
        defaultColors = [default_black_color,
            default_white_color
        ]

        pending_colors_array = []
        for aPotentialNewColor in defaultColors:
            if (not (aPotentialNewColor.hex_color in self.colorsDict.keys())):
                pending_colors_array.append(aPotentialNewColor)

        self.database_connection.save_colors_to_database(pending_colors_array)
        self.colorsDict = self.database_connection.load_colors_from_database()

        # For adding to the DB
        behaviorGroupsDBList = []
        behaviorsDBList = []

        # Add the top-level parent nodes
        for (aTypeId, aUniqueBehavior) in enumerate(self.behaviorsManager.get_unique_behavior_groups()):
            aNewNode = QTreeWidgetItem([aUniqueBehavior, str(aTypeId), "String C"])
            aNodeColor = self.behaviorsManager.groups_color_dictionary[aUniqueBehavior]
            aNewNode.setBackground(0, aNodeColor)
            self.topLevelNodes.append(aNewNode)
            self.topLeftNodesDict[aUniqueBehavior] = (len(self.topLevelNodes)-1) # get the index of the added node

            aNodeColorHexID = aNodeColor.name(QColor.HexRgb)
            if (not (aNodeColorHexID in self.colorsDict.keys())):
                # If the color is new, add it to the color table in the database
                aDBColor = CategoryColors(None, aNodeColorHexID, aUniqueBehavior, ('Created for ' + aUniqueBehavior), aNodeColor.red(), aNodeColor.green(), aNodeColor.blue(), 'Auto-generated')
                self.database_connection.save_colors_to_database([aDBColor])
                self.colorsDict = self.database_connection.load_colors_from_database()
            else:
                #Else get the existing color
                aDBColor = self.colorsDict[aNodeColorHexID]
                            
            if (not aDBColor.id):
                print("INVALID COLOR ID!")

            aNewDBNode = BehaviorGroup(None, aUniqueBehavior, aUniqueBehavior, aDBColor.id, default_black_color.id, 'auto')

            behaviorGroupsDBList.append(aNewDBNode)

        # Add the leaf nodes
        for (aSubtypeID, aUniqueLeafBehavior) in enumerate(self.behaviorsManager.get_unique_behaviors()):
            parentNodeName = self.behaviorsManager.leaf_to_behavior_groups_dict[aUniqueLeafBehavior]
            parentNodeIndex = self.topLeftNodesDict[parentNodeName]
            parentNode = self.topLevelNodes[parentNodeIndex]
            if parentNode:
                # found parent
                aNewNode = QTreeWidgetItem([aUniqueLeafBehavior, "(type: {0}, subtype: {1})".format(str(parentNodeIndex), str(aSubtypeID)), parentNodeName])
                aNodeColor = self.behaviorsManager.color_dictionary[aUniqueLeafBehavior]
                aNewNode.setBackground(0, aNodeColor)
                parentNode.addChild(aNewNode)

                aNodeColorHexID = aNodeColor.name(QColor.HexRgb)
                if (not (aNodeColorHexID in self.colorsDict.keys())):
                    # If the color is new, add it to the color table in the database
                    aDBColor = CategoryColors(None, aNodeColorHexID, aUniqueLeafBehavior, ('Created for ' + aUniqueLeafBehavior), aNodeColor.red(), aNodeColor.green(), aNodeColor.blue(), 'Auto-generated')
                    self.database_connection.save_colors_to_database([aDBColor])
                    self.colorsDict = self.database_connection.load_colors_from_database()
                else:
                    #Else get the existing color
                    aDBColor = self.colorsDict[aNodeColorHexID]

                # Get parent node
                parentDBNode = behaviorGroupsDBList[parentNodeIndex]
                if (not parentDBNode):
                    print("Couldn't find parent node!")
                    parent_node_db_id = None
                else:
                    if parentDBNode.id:
                        print("Found parent with index {0}".format(parentDBNode.id))
                        parent_node_db_id = parentDBNode.id
                    else:
                        print("couldn't get parent node's .id property, using the index {0}".format(parentNodeIndex + 1))
                        parent_node_db_id = int(parentNodeIndex + 1)

                aNewDBNode = Behavior(None, aUniqueLeafBehavior, aUniqueLeafBehavior, parent_node_db_id, aDBColor.id, default_black_color.id, 'auto')

                behaviorsDBList.append(aNewDBNode)

            else:
                print('Failed to find the parent node with name: ', parentNodeName)
            
        self.ui.treeWidget_Settings_PartitionTrack.addTopLevelItems(self.topLevelNodes)
        
        self.database_connection.save_behavior_events_to_database(behaviorsDBList, behaviorGroupsDBList)
        return 


    # Called to rebuild the behaviors tree and table from the behaviors data loaded from the database
    def build_behaviors_interfaces_from_loaded(self):
        
        # Table
        self.ui.tableWidget_Settings_PartitionTrack.clear()
        self.partitionInfoOptions = []
        
        # Tree
        self.ui.treeWidget_Settings_PartitionTrack.clear()
        self.topLevelNodes = []
        self.topLeftNodesDict = dict()

         # Add the top-level parent nodes
        for (aTypeId, aUniqueBehaviorGroup) in enumerate(self.behaviorGroups):
            # Get loaded item properties
            if aUniqueBehaviorGroup.description:
                extra_string = aUniqueBehaviorGroup.description
            else:
                extra_string = "String C"

            aNewGroupNode = QTreeWidgetItem([aUniqueBehaviorGroup.name, str(aTypeId), extra_string])
            aNodeColor = aUniqueBehaviorGroup.primaryColor.get_QColor()
            aNewGroupNode.setBackground(0, aNodeColor)

            # Table Item:
            newObj = BehaviorInfoOptions(aUniqueBehaviorGroup.name, aUniqueBehaviorGroup.name, aTypeId, 0, aNodeColor)
            self.partitionInfoOptions.append(newObj)

            for (aSubtypeID, aUniqueLeafBehavior) in enumerate(aUniqueBehaviorGroup.behaviors):
                if aUniqueLeafBehavior.description:
                    extra_string = aUniqueLeafBehavior.description
                else:
                    # Otherwise it's the parents' name
                    extra_string = aUniqueBehaviorGroup.name

                aNewNode = QTreeWidgetItem([aUniqueLeafBehavior.name, "(type: {0}, subtype: {1})".format(str(aTypeId), str(aSubtypeID)), extra_string])
                aNodeColor = aUniqueLeafBehavior.primaryColor.get_QColor()
                aNewNode.setBackground(0, aNodeColor)
                aNewGroupNode.addChild(aNewNode)

            self.topLevelNodes.append(aNewGroupNode)
            
        self.ui.treeWidget_Settings_PartitionTrack.addTopLevelItems(self.topLevelNodes)
        # Refresh the table to display the updated data
        self.updatePartitionOptionsTable()


    # Initializes the UI elements that display/edit the behaviors
    def initBehaviorsInterfaces(self):

        # Load the latest behaviors and colors data from the database
        self.colorsDict = self.database_connection.load_colors_from_database()
        self.behaviorGroups = self.database_connection.load_behaviors_from_database()

        # Determine if we need to initialize a sample color/behavior database
        needs_init_sample_db = True

        if self.colorsDict and self.behaviorGroups:
            # Valid loaded objects
            if (len(self.behaviorGroups) > 0):
                needs_init_sample_db = False
            
        # Initializes the DB if that's needed (if it's empty)
        if needs_init_sample_db:
            self.initSampleBehaviorsDatabase()
        
        # Build the UI objects either way
        self.build_behaviors_interfaces_from_loaded()

        self.database_connection.close()


    # Updates the table interface from the self.partitionInfoObjects variable
    def updatePartitionOptionsTable(self):
        # Setup Table
        self.ui.tableWidget_Settings_PartitionTrack.setColumnCount(5)
        self.ui.tableWidget_Settings_PartitionTrack.setRowCount(len(self.partitionInfoOptions)+1)
        # Headers
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,0,QTableWidgetItem("Name"))
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,1,QTableWidgetItem("Descr."))
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,2,QTableWidgetItem("Type"))
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,3,QTableWidgetItem("Subtype"))
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,4,QTableWidgetItem("Color"))

        for (aRowIndex, aPartitionInfoOption) in enumerate(self.partitionInfoOptions):
            aDataRowIndex = aRowIndex + 1 # Add one to compensate for the header row
            # self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,0,QTableWidgetItem(str(aRowIndex)))
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,0,QTableWidgetItem(aPartitionInfoOption.name))
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,1,QTableWidgetItem(aPartitionInfoOption.description))
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,2,QTableWidgetItem(str(aPartitionInfoOption.type)))
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,3,QTableWidgetItem(str(aPartitionInfoOption.subtype)))

            # Color Item:
            currColorTableWidgetItem = QTableWidgetItem('')
            currColorTableWidgetItem.setBackground(aPartitionInfoOption.color)
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,4,currColorTableWidgetItem)


    # Seems to be called programmatically when the table items are added
    def on_item_changed(self, item):
        # print('on_item_changed() table item (col: {0}, row: {1}): content: {2}'.format(item.column(), item.row(), item.text()))

        if (self.behaviorsTableEditingIndex):
            # print("Editing index: {0}".format(self.behaviorsTableEditingIndex))
            # If we have an active editing index, see if it matches the changed item, implying the user has edited it
            if ((self.behaviorsTableEditingIndex[0] == item.column()) and (self.behaviorsTableEditingIndex[1] == item.row())):
                # Item matches editing item, user might have changed it
                print("User changed item!")
            else:
                # Otherwise, the user activated a new item without editing the edit item, so the editing item is None
                # print("User didn't edit item")
                pass

            # After this, editing is done, so we set the editing index back to None
            self.behaviorsTableEditingIndex = None
        else:
            # print("Not editing")
            pass


    # This is being called whenever the table selection is updated, independent of if the contents of the cell are being edited
    def on_current_item_changed(self, item):
        # print('on_current_item_changed() table item (col: {0}, row: {1}): content: {2}'.format(item.column(), item.row(), item.text()))
        self.behaviorsTableActiveIndex = (item.column(), item.row())



    # Called upon starting to edit a table cell
    def editItem(self, item):
        # print('editItem() table item (col: {0}, row: {1}): content: {2}'.format(item.column(), item.row(), item.text()))
        self.behaviorsTableEditingIndex = (item.column(), item.row())
        
        # column is 0-indexed
        if (item.column() == 1):
            # Description Column
            print('Description column: editing')
            # self.current_editing_item_row = item.row()
            # self.current_editing_item_old_value = item.text()
            oldValue = item.text()
            # newValue = item.text()
            # print('old value: {0}'.format(oldValue))


        elif (item.column() == 4):
            print('Color column: selecting')
            newRowColor = self.color_picker()
            if newRowColor:
                self.partitionInfoOptions[item.row()-1].color = newRowColor
                # Update the row color
                item.setBackground(newRowColor)
                print('Color updated!')
        else:
            print('editItem() table item {0}: Unknown action'.format(item.text())) 

    

    def color_picker(self):
        color = QColorDialog.getColor()
        return color
        # self.styleChoice.setStyleSheet("QWidget { background-color: %s}" % color.name())

