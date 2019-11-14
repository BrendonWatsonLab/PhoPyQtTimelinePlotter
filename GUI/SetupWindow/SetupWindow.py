# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timezone, timedelta
# import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, qApp, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog, QTreeWidget, QTreeWidgetItem, QDialogButtonBox, QMessageBox, QStyledItemDelegate, QStyle
# from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPalette
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef
from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWindow

from app.BehaviorsList import BehaviorsManager, BehaviorInfoOptions
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors

# from GUI.UI.EditCapableTableView import EditCapableTableView

# Enables not painting the background on selection for the color cells.
# https://stackoverflow.com/questions/47880568/how-to-set-each-items-selection-color-of-qtablewidget-in-pyqt5
class ColorDelegate(QStyledItemDelegate):
    DefaultSelectionColor = QColor(41, 142, 230, 200) # A mid-darkish blue with 200/255 opacity

    def paint(self, painter, option, index):
        color = index.data(Qt.UserRole) or ColorDelegate.DefaultSelectionColor
        option.palette.setColor(QPalette.Highlight, color)
        QStyledItemDelegate.paint(self, painter, option, index)


class SetupWindow(AbstractDatabaseAccessingWindow):
    def __init__(self, database_connection):
        super(SetupWindow, self).__init__(database_connection) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/SetupWindow/SetupWindow.ui", self) # Load the .ui file
        self.behaviorsManager = BehaviorsManager()

        # The most recently selected/activated table cell index (column, row) or None
        self.behaviorsTableActiveIndex = None

        # The table index currently being edited
        self.behaviorsTableEditingIndex = None

        # A variable to represent a reference to a QMessageBox dialog that's temporarily displayed.
        self.activeMessageBox = None

        self.user_edited_pending_counts = self.database_connection.get_pending_counts()

        self.initUI()

    def initUI(self):
        
        # self.ui.tableWidget_Settings_PartitionTrack.setH

        # if you don't want to allow in-table editing, either disable the table like:
        # self.ui.tableWidget_Settings_PartitionTrack.setEditTriggers(QTableWidget.NoEditTriggers)

        # or specifically for this item
        # self.ui.tableWidget_Settings_PartitionTrack.setFlags(item.flags() ^ Qt.ItemIsEditable)

        # create a connection to the double click event
        self.ui.tableWidget_Settings_PartitionTrack.setItemDelegate(ColorDelegate())
        self.ui.tableWidget_Settings_PartitionTrack.itemDoubleClicked.connect(self.on_begin_edit_behavior_table_item)

        # Not sure which function I want to use
        self.ui.tableWidget_Settings_PartitionTrack.itemChanged.connect(self.on_behavior_table_item_changed)
        self.ui.tableWidget_Settings_PartitionTrack.currentItemChanged.connect(self.on_current_behavior_table_item_changed)

        self.ui.buttonBox_Settings_PartitionTrack.clicked.connect(self.on_update_buttonBox_clicked)

        # self.setStyleSheet("QTableView{ selection-background-color: rgba(255, 0, 0, 50);  }")
        # self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.reloadBehaviorsInterfaces(should_initialize_database_from_sample_if_missing=False)



## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        self.colorsDict = self.database_connection.load_colors_from_database()
        self.behaviorGroups = self.database_connection.load_behaviors_from_database()
        ## What about self.partitionInfoOptions?
        

## General Functions:

    # Creates both the behavior tree and the behaviors database from a set of hard-coded values defined in behaviorsManager
    def initSampleBehaviorsDatabase(self):
        print("INITIALIZING SAMPLE BEHAVIORS DATABASE")
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
        # self.ui.tableWidget_Settings_PartitionTrack.clear()
        self.ui.tableWidget_Settings_PartitionTrack.clearContents()
        
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
            newObj = BehaviorInfoOptions(aUniqueBehaviorGroup.name, (aUniqueBehaviorGroup.description or aUniqueBehaviorGroup.name), aTypeId, 0, aNodeColor)
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
    # If should_initialize_database_from_sample_if_missing is true, the database will attempt to be loaded, and if that fails or it's empty it will be created from sample data
    def reloadBehaviorsInterfaces(self, should_initialize_database_from_sample_if_missing):

        # Load the latest behaviors and colors data from the database
        self.reloadModelFromDatabase()

        if should_initialize_database_from_sample_if_missing:
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

        # self.database_close()


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
            currColorTableWidgetItem.setFlags(currColorTableWidgetItem.flags() ^ Qt.ItemIsEditable)
            currColorTableWidgetItem.setData(Qt.UserRole, aPartitionInfoOption.color) # Set the color as user data on the item
            # "selection-background-color: #000000;"
            self.ui.tableWidget_Settings_PartitionTrack.setItem(aDataRowIndex,4,currColorTableWidgetItem)

    # Called when the user edited an item
    def on_user_updated_behavior_table_item(self, column, row, newValue):
        # self.get_has_pending_changes()        
        # self.reloadModelFromDatabase()
        did_change_occur = False

        if column == 0:
            # Name column:
            pass
        elif column == 1:
            # Description column:
            prevValue = self.behaviorGroups[row-1].description
            # prevValue = self.behaviorsTableEditingPrevValue
            if (newValue == prevValue):
                print("Unchanged from original!")
                return
            else:
                print("Value changed from {0} to {1}".format(prevValue, newValue))
                self.behaviorGroups[row-1].description = newValue
                did_change_occur = True
        elif column == 4:
            # Color column
            pass

        else:
            # Other column
            pass

        if did_change_occur:
            # Conditionally enable/disable save/revert buttons

            # Rebuild the table and tree
            # self.build_behaviors_interfaces_from_loaded()

            pass
        else:
            pass
            # self.database_close()

    ## Handlers:

    # Seems to be called programmatically when the table items are added
    def on_behavior_table_item_changed(self, item):
        # print('on_item_changed() table item (col: {0}, row: {1}): content: {2}'.format(item.column(), item.row(), item.text()))

        if (self.behaviorsTableEditingIndex):
            # print("Editing index: {0}".format(self.behaviorsTableEditingIndex))
            # If we have an active editing index, see if it matches the changed item, implying the user has edited it
            if ((self.behaviorsTableEditingIndex[0] == item.column()) and (self.behaviorsTableEditingIndex[1] == item.row())):
                # Item matches editing item, user might have changed it
                print("User changed item!")
                self.on_user_updated_behavior_table_item(item.column(), item.row(), item.text())
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
    def on_current_behavior_table_item_changed(self, item):
        # print('on_current_item_changed() table item (col: {0}, row: {1}): content: {2}'.format(item.column(), item.row(), item.text()))
        if item:
            self.behaviorsTableActiveIndex = (item.column(), item.row())
        else:
            # No selection
            self.behaviorsTableEditingIndex = None

    # Called upon starting to edit a table cell
    def on_begin_edit_behavior_table_item(self, item):
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
            # Get the existing table item color
            original_item_color = item.background().color()
            newRowColor = self.open_color_picker(original_item_color)
            if newRowColor:
                self.partitionInfoOptions[item.row()-1].color = newRowColor
                # Update the row color
                item.setBackground(newRowColor)
                item.setData(Qt.UserRole, newRowColor) # Set the color as user data on the item
                print('Color updated!')
        else:
            print('editItem() table item {0}: Unknown action'.format(item.text())) 

    # Called when one of the buttons in the button box at the bottom of the window are clicked like "Save all", "Reset", or "Restore Defaults"
    def on_update_buttonBox_clicked(self, button):
        sb = self.ui.buttonBox_Settings_PartitionTrack.standardButton(button)
        self.user_edited_pending_counts = self.database_connection.get_pending_counts()

        if sb == QDialogButtonBox.SaveAll:
            print('SaveAll Clicked')
            print("Saving {0} changes...".format(str(self.user_edited_pending_counts)))
            self.database_connection.commit()
            self.reloadModelFromDatabase()
            self.build_behaviors_interfaces_from_loaded()

        elif sb == QDialogButtonBox.Reset:
            print('Reset Clicked')
            self.reloadBehaviorsInterfaces(should_initialize_database_from_sample_if_missing=False)

        elif sb == QDialogButtonBox.RestoreDefaults:
            print("RestoreDefaults Clicked")
            self.open_confirm_restore_defaults_messagebox()
        else:
            print("UNIMPLEMENTED: Unhandled button box button")
        # and so on...
    


## UTILITY Functions:

    # Opens a dialog that asks the user to confirm the "Restore Defaults" operation.
    def open_confirm_restore_defaults_messagebox(self):
        self.activeMessageBox = QMessageBox()
        self.activeMessageBox.setIcon(QMessageBox.Warning)

        self.activeMessageBox.setText("This will overwrite the data in the database with the sample data that was hard-coded into the application.")
        self.activeMessageBox.setInformativeText("You probably don't want to do this unless the database has become corrupted or you're testing!")
        self.activeMessageBox.setWindowTitle("Restore Sample Data?")
        # msg.setDetailedText("The details are as follows:")
        self.activeMessageBox.setStandardButtons(QMessageBox.RestoreDefaults | QMessageBox.Cancel)
        self.activeMessageBox.setDefaultButton(QMessageBox.Cancel)
        self.activeMessageBox.buttonClicked.connect(self.on_confirm_restore_defaults_messagebox_callback)
        
        retval = self.activeMessageBox.exec_()
        # print("value of pressed message box button:", retval)
        

    # Callback of the "Restore Defaults" confirmatory message box
    def on_confirm_restore_defaults_messagebox_callback(self, button):
        print("Button pressed is:",button.text())
        button = self.activeMessageBox.standardButton(button)
        # sb = self.ui.buttonBox_Settings_PartitionTrack.standardButton(button)
        if button == QMessageBox.RestoreDefaults:
            print('Confirm RestoreDefaults Clicked')
        elif button == QMessageBox.Cancel:
            print('Cancel Clicked')
        else:
            print("UNIMPLEMENTED: Unhandled QMessageBox button")

        # Clear the messagebox variable
        self.activeMessageBox = None
        


        


    # Displays a color-picker window that the user can select a color from
    def open_color_picker(self, existingColor):
        color = QColorDialog.getColor(existingColor, self)
        if color:
            if color.isValid():
                return color
            else:
                # User canceled
                print("User canceled color selection.")
                return None
        else:
            return None

