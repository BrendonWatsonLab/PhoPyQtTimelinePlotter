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

class SetupWindow(AbstractDatabaseAccessingWindow):
    def __init__(self, database_connection):
        super(SetupWindow, self).__init__(database_connection) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/SetupWindow/SetupWindow.ui", self) # Load the .ui file
        self.behaviorsManager = BehaviorsManager()

        self.build_from_behaviors_manager()
        self.initUI()

    def initUI(self):
        self.ui.tableWidget_Settings_PartitionTrack.setColumnCount(5)
        self.ui.tableWidget_Settings_PartitionTrack.setRowCount(len(self.partitionInfoOptions)+1)
        # Headers
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,0,QTableWidgetItem("Name"))
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,1,QTableWidgetItem("Descr."))
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,2,QTableWidgetItem("Type"))
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,3,QTableWidgetItem("Subtype"))
        self.ui.tableWidget_Settings_PartitionTrack.setItem(0,4,QTableWidgetItem("Color"))
        # self.ui.tableWidget_Settings_PartitionTrack.setH

        # if you don't want to allow in-table editing, either disable the table like:
        self.ui.tableWidget_Settings_PartitionTrack.setEditTriggers(QTableWidget.NoEditTriggers)

        # or specifically for this item
        # self.ui.tableWidget_Settings_PartitionTrack.setFlags(item.flags() ^ Qt.ItemIsEditable)

        # create a connection to the double click event
        self.ui.tableWidget_Settings_PartitionTrack.itemDoubleClicked.connect(self.editItem)
        self.updatePartitionOptionsTable()

        self.initBehaviorsTree()

    def build_from_behaviors_manager(self):
        # uniqueBehaviorsList = self.behaviorsManager.get_unique_behaviors()
        # uniqueColorsDict = self.behaviorsManager.color_dictionary
        uniqueBehaviorsList = self.behaviorsManager.get_unique_behavior_groups()
        uniqueColorsDict = self.behaviorsManager.groups_color_dictionary
        
        self.partitionInfoOptions = []
        for (anIndex, aBehavior) in enumerate(uniqueBehaviorsList):
            newObj = BehaviorInfoOptions(aBehavior, aBehavior, anIndex, 0, uniqueColorsDict[aBehavior])
            self.partitionInfoOptions.append(newObj)

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


    # Called to rebuild the behaviors tree from the behaviors data loaded from the database
    def build_behaviors_tree_from_loaded(self):
        
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

    def initBehaviorsTree(self):

        # Load the latest behaviors and colors data from the database
        self.colorsDict = self.database_connection.load_colors_from_database()
        self.behaviorGroups = self.database_connection.load_behaviors_from_database()

        # Determine if we need to initialize a sample color/behavior database
        needs_init_sample_db = True

        if self.colorsDict and self.behaviorGroups:
            # Valid loaded objects
            if (len(self.behaviorGroups) > 0):
                needs_init_sample_db = False
            

        if needs_init_sample_db:
            self.initSampleBehaviorsDatabase()
        else:
            self.build_behaviors_tree_from_loaded()        

        self.database_connection.close()


    def updatePartitionOptionsTable(self):
        for (aRowIndex, aPartitionInfoOption) in enumerate(self.partitionInfoOptions):
            aDataRowIndex = aRowIndex + 1 # Add one to compensate for the header row
            # self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,0,QTableWidgetItem(str(aRowIndex)))
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,0,QTableWidgetItem(aPartitionInfoOption.name))
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,1,QTableWidgetItem(aPartitionInfoOption.description))
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,2,QTableWidgetItem(str(aPartitionInfoOption.type)))
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,3,QTableWidgetItem(str(aPartitionInfoOption.subtype)))

            # Color Item:
            currColorTableWidgetItem = QTableWidgetItem('')
            # btnCurrTableWidgetCellColorItem = QPushButton(self.ui.tableWidget_Settings_PartitionTrack)
            # # btnCurrTableWidgetCellColorItem = QPushButton(currColorTableWidgetItem)
            # btnCurrTableWidgetCellColorItem.setText('color')
            # btnCurrTableWidgetCellColorItem.setAutoFillBackground(True)
            # btnCurrTableWidgetCellColorItem.setStyleSheet("background-color: red")
            # # btnCurrTableWidgetCellColorItem.clicked.connect(self.color_picker)

            # currColorTableWidgetItem.itemDoubleClicked.connect(self.editItem)
            # currColorTableWidgetItem.setFlags(currColorTableWidgetItem.flags() ^ Qt.ItemIsEditable)
            currColorTableWidgetItem.setBackground(aPartitionInfoOption.color)
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,4,currColorTableWidgetItem)
            # self.ui.tableWidget_Settings_PartitionTrack.setCellWidget(aDataRowIndex, 4, btnCurrTableWidgetCellColorItem)


    def editItem(self, item):        
        if (item.column() == 4):
            print('Color column: selecting')
            newRowColor = self.color_picker()
            if newRowColor:
                self.partitionInfoOptions[item.row()-1].color = newRowColor
                # Update the row color
                item.setBackground(newRowColor)
                print('Color updated!')
        else:
            print('editing table item {0}'.format(item.text())) 

    

    def color_picker(self):
        color = QColorDialog.getColor()
        return color
        # self.styleChoice.setStyleSheet("QWidget { background-color: %s}" % color.name())

