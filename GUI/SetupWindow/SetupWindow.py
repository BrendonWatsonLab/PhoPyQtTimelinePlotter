# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timezone, timedelta
# import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog, QTreeWidget, QTreeWidgetItem
# from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize


from app.BehaviorsList import BehaviorsManager, BehaviorInfoOptions

class SetupWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(SetupWindow, self).__init__() # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/SetupWindow/SetupWindow.ui", self) # Load the .ui file
        self.behaviorsManager = BehaviorsManager()
        # self.partitionInfoOptions = [PartitionInfoOptions('Unpartitioned','Unpartitioned'),
        #     PartitionInfoOptions('Removed','Removed'),
        #     PartitionInfoOptions('Sleep','Sleep'),
        #     PartitionInfoOptions('Stationary','Stationary'),
        #     PartitionInfoOptions('Active','Active'),
        #     PartitionInfoOptions('Running','Running')
        # ]

        # self.partitionInfoOptions = [PartitionInfoOptions('Unpartitioned','Unpartitioned'),
        #     PartitionInfoOptions('Removed','Removed'),
        #     PartitionInfoOptions('Sleep','Sleep'),
        #     PartitionInfoOptions('Stationary','Stationary'),
        #     PartitionInfoOptions('Active','Active'),
        #     PartitionInfoOptions('Running','Running')
        # ]

        self.build_from_behaviors_manager()
        self.initUI()

    def build_from_behaviors_manager(self):
        # uniqueBehaviorsList = self.behaviorsManager.get_unique_behaviors()
        # uniqueColorsDict = self.behaviorsManager.color_dictionary
        uniqueBehaviorsList = self.behaviorsManager.get_unique_behavior_groups()
        uniqueColorsDict = self.behaviorsManager.groups_color_dictionary
        
        self.partitionInfoOptions = []
        for (anIndex, aBehavior) in enumerate(uniqueBehaviorsList):
            newObj = BehaviorInfoOptions(aBehavior, aBehavior, anIndex, 0, uniqueColorsDict[aBehavior])
            self.partitionInfoOptions.append(newObj)

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

        self.topLevelNodes = []
        self.topLeftNodesDict = dict()

        # Add the top-level parent nodes
        for (aTypeId, aUniqueBehavior) in enumerate(self.behaviorsManager.get_unique_behavior_groups()):
            aNewNode = QTreeWidgetItem([aUniqueBehavior, str(aTypeId), "String C"])
            
            aNewNode.setBackground(0, self.behaviorsManager.groups_color_dictionary[aUniqueBehavior])
            self.topLevelNodes.append(aNewNode)
            self.topLeftNodesDict[aUniqueBehavior] = (len(self.topLevelNodes)-1) # get the index of the added node

        # Add the leaf nodes
        for (aSubtypeID, aUniqueLeafBehavior) in enumerate(self.behaviorsManager.get_unique_behaviors()):
            parentNodeName = self.behaviorsManager.leaf_to_behavior_groups_dict[aUniqueLeafBehavior]
            parentNodeIndex = self.topLeftNodesDict[parentNodeName]
            parentNode = self.topLevelNodes[parentNodeIndex]
            if parentNode:
                # found parent
                aNewNode = QTreeWidgetItem([aUniqueLeafBehavior, "(type: {0}, subtype: {1})".format(str(parentNodeIndex), str(aSubtypeID)), parentNodeName])
                aNewNode.setBackground(0, self.behaviorsManager.color_dictionary[aUniqueLeafBehavior])
                parentNode.addChild(aNewNode)
            else:
                print('Failed to find the parent node with name: ', parentNodeName)
            
        self.ui.treeWidget_Settings_PartitionTrack.addTopLevelItems(self.topLevelNodes)


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

