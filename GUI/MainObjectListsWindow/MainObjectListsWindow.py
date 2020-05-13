# EventsDrawingWindow.py
# Draws the main window containing several EventTrackDrawingWidgets

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QAction, qApp, QApplication, QTreeWidgetItem, QFileDialog 
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir, QThreadPool, QVariant

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWindow

from app.filesystem.VideoUtils import findVideoFiles, VideoParsedResults, FoundVideoFileResult, CachedFileSource
# from app.filesystem.Workers.VideoMetadataWorkers import VideoMetadataWorker, VideoMetadataWorkerSignals
# from app.filesystem.Workers.VideoFilesystemWorkers import VideoFilesystemWorker, VideoFilesystemWorkerSignals

from pathlib import Path

from app.database.entry_models.db_model import FileParentFolder, StaticFileExtension, VideoFile
from app.filesystem.VideoConversionHelpers import HandbrakeConversionQueue, save_handbrake_conversion_queue

from app.filesystem.VideoFilesystemLoadingMixin import CachedVideoFileLoadingOptions, ParentDirectoryCache, VideoFilesystemLoader
from app.filesystem.DeeplabcutOutputFilesystemLoadingMixin import DeeplabCutOutputFileType, DeeplabcutEventFile, DeeplabcutFilesystemLoader

# Pandas dataframe tables
from GUI.Model.TableModels.PandasTableModel import PandasTableModel
from GUI.UI.TableWidgets.PandasTableWidget import PandasTableWidget

class MainObjectListsWindow(AbstractDatabaseAccessingWindow):

    VideoFileTreeHeaderLabels = ['filename', 'start_date', 'end_date', 'is_labeled']
    
    # VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadOnlyFromDatabase
    VideoFileLoadingMode = CachedVideoFileLoadingOptions.LoadDatabaseAndSearchVideoFileSearchPaths
    

    TreeItem_Default_Font = QtGui.QFont("Times", 9)
    TreeItem_Default_Foreground = QBrush(Qt.black)

    TreeItem_Emphasized_Font = QtGui.QFont("Times", 11)
    TreeItem_Emphasized_Foreground = QBrush(Qt.darkBlue)

    TreeItem_DatabaseOnly_Foreground = QBrush(Qt.blue)
    TreeItem_FilesystemOnly_Foreground = QBrush(Qt.green)
    TreeItem_FilesystemNewer_Foreground = QBrush(Qt.darkGreen)
    TreeItem_DatabaseNewer_Foreground = QBrush(Qt.darkBlue)

    def __init__(self, database_connection, videoFileSearchPaths):
        super(MainObjectListsWindow, self).__init__(database_connection) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/MainObjectListsWindow/MainObjectListsWindow.ui", self) # Load the .ui file
        self.videoLoader = VideoFilesystemLoader(self.database_connection, videoFileSearchPaths, parent=self)
        self.videoLoader.foundFilesUpdated.connect(self.rebuild_from_found_files)
        self.videoLoader.findFilesInSearchDirectoryComplete.connect(self.on_update_search_path)
        # self.reload_on_search_paths_changed()

        self.top_level_nodes = []
        self.currentTablePreviewWidget = None

        self.setMouseTracking(True)
        self.initUI()

        self.reload_data()
        
    def initUI(self):

        """ View Hierarchy:
        ...TODO
        """

        # Nested helper function to initialize the menu bar
        def initUI_initMenuBar(self):
            self.ui.actionLoad.triggered.connect(self.handle_menu_load_event)
            self.ui.actionSave.triggered.connect(self.handle_menu_save_event)
            self.ui.actionRefresh.triggered.connect(self.handle_menu_refresh_event)
            
        desiredWindowWidth = 500
        self.resize( desiredWindowWidth, 800 )

        # Setup the menubar
        initUI_initMenuBar(self)

        # Setup the tree
        # self.ui.treeWidget_VideoFiles
        self.ui.treeWidget_VideoFiles.setHeaderLabels(MainObjectListsWindow.VideoFileTreeHeaderLabels)
        # Connect the tree widget's contextmenu
        self.ui.treeWidget_VideoFiles.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeWidget_VideoFiles.customContextMenuRequested.connect(self.menuContextTree)



        self.ui.textBrowser_SelectedInfoBox.setText("Hi")

        # Main Vertical Splitter:
        self.ui.mainVerticalSplitter.setSizes([700, 100])

        # Setup the buttons
        self.ui.pushButton_AddSearchDirectory.clicked.connect(self.handle_add_search_directory_activated)
        self.ui.toolButton_Load.clicked.connect(self.handle_menu_load_event)
        self.ui.toolButton_SaveSelected.clicked.connect(self.handle_save_selection_action)
        self.ui.toolButton_GetConversionList.clicked.connect(self.handle_get_conversion_list_action)

        # Complete setup
        self.statusBar()


    def reload_on_search_paths_changed(self):
         self.videoLoader.reload_on_search_paths_changed()

    def get_video_loader(self):
        return self.videoLoader

    def reload_data(self):
        self.videoLoader.reload_data()

    # TODO: should build parent nodes from a combination of the loaded parents and the search paths (if we're in a mode to load search paths)
    
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        self.videoLoader.reloadModelFromDatabase()

    def saveVideoFilesToDatabase(self):
        self.videoLoader.saveVideoFilesToDatabase()


    # Rebuilds the entire Tree UI from the self.found_files_lists
    @pyqtSlot()
    def rebuild_from_found_files(self):
        self.ui.treeWidget_VideoFiles.clear()
        self.top_level_nodes = []

        # Clear the top-level nodes
        # for (aSearchPathIndex, aSearchPath) in enumerate(self.searchPaths):
        for (key_path, cache_value) in self.get_video_loader().get_cache().items():        
            aNewGroupNode = QTreeWidgetItem([key_path, '', '', ''])
            # curr_search_path_video_files = cache_value.get_filesystem_video_files()
            curr_search_path_video_files = cache_value.get_combined_video_files()
            curr_search_path_data_file_map = cache_value.get_combined_video_file_basenames_to_data_file_list_map()
            curr_search_path_output_data_files = []

            print("ui loadedVideoFiles[{0}]: {1}".format(str(key_path), len(curr_search_path_video_files)))

            for aFoundVideoFile in curr_search_path_video_files:
                aCurrVideoFileBasename = aFoundVideoFile.get_base_name()

                potentially_computed_end_date = aFoundVideoFile.get_computed_end_date()
                if potentially_computed_end_date:
                    computed_end_date = str(potentially_computed_end_date)
                else:
                    computed_end_date = 'Loading...'
                aNewVideoNode = QTreeWidgetItem([str(aFoundVideoFile.full_name), str(aFoundVideoFile.parsed_date), computed_end_date, str(aFoundVideoFile.is_deeplabcut_labeled_video)])
                # aNewVideoNode.setIcon(0,QIcon("your icon path or file name "))

                currSource = aFoundVideoFile.get_source()
                currForeground = MainObjectListsWindow.TreeItem_Default_Foreground
                currFont = MainObjectListsWindow.TreeItem_Default_Font

                if currSource == CachedFileSource.OnlyFromDatabase:
                    currForeground = MainObjectListsWindow.TreeItem_DatabaseOnly_Foreground
                    pass
                elif currSource == CachedFileSource.OnlyFromFilesystem:
                    currForeground = MainObjectListsWindow.TreeItem_FilesystemOnly_Foreground
                    pass
                elif currSource == CachedFileSource.NewestFromDatabase:
                    currForeground = MainObjectListsWindow.TreeItem_DatabaseNewer_Foreground
                    pass
                elif currSource == CachedFileSource.NewestFromFilesystem:
                    currForeground = MainObjectListsWindow.TreeItem_FilesystemNewer_Foreground
                    pass
                elif currSource == CachedFileSource.Identical:
                    currForeground =  MainObjectListsWindow.TreeItem_Default_Foreground
                    pass
                else:
                    pass

                aNewVideoNode.setForeground(0, currForeground)
                aNewVideoNode.setFont(0, currFont)
                
                # Check for data files:
                curr_video_file_output_data_files = []
                if aCurrVideoFileBasename in curr_search_path_data_file_map.keys():
                    curr_video_file_output_data_files = curr_search_path_data_file_map[aCurrVideoFileBasename]

                # print("ui loadedVideoFiles[{0}]: {1}".format(str(key_path), len(curr_video_file_output_data_files)))
                for aFoundDataFile in curr_video_file_output_data_files:
                    aNewDataNode = QTreeWidgetItem([str(aFoundDataFile.full_name), str(aFoundDataFile.parsed_date), computed_end_date, str(aFoundDataFile.get_deeplabcut_info_string())])
                    aNewDataNode.setData(0, Qt.UserRole, aFoundDataFile)

                    # aNewVideoNode.setIcon(0,QIcon("your icon path or file name "))

                    currSource = aFoundDataFile.get_source()
                    currForeground = MainObjectListsWindow.TreeItem_Default_Foreground
                    currFont = MainObjectListsWindow.TreeItem_Default_Font

                    if currSource == CachedFileSource.OnlyFromDatabase:
                        currForeground = MainObjectListsWindow.TreeItem_DatabaseOnly_Foreground
                        pass
                    elif currSource == CachedFileSource.OnlyFromFilesystem:
                        currForeground = MainObjectListsWindow.TreeItem_FilesystemOnly_Foreground
                        pass
                    elif currSource == CachedFileSource.NewestFromDatabase:
                        currForeground = MainObjectListsWindow.TreeItem_DatabaseNewer_Foreground
                        pass
                    elif currSource == CachedFileSource.NewestFromFilesystem:
                        currForeground = MainObjectListsWindow.TreeItem_FilesystemNewer_Foreground
                        pass
                    elif currSource == CachedFileSource.Identical:
                        currForeground =  MainObjectListsWindow.TreeItem_Default_Foreground
                        pass
                    else:
                        pass

                    aNewDataNode.setForeground(0, currForeground)
                    aNewDataNode.setFont(0, currFont)
                    
                    aNewVideoNode.addChild(aNewDataNode)

                # Add the new video node to the group
                aNewGroupNode.addChild(aNewVideoNode)


            self.top_level_nodes.append(aNewGroupNode)
            
            # Eventually will call .parse() on each of them to populate the duration info and end-times. This will be done asynchronously.
        self.ui.treeWidget_VideoFiles.addTopLevelItems(self.top_level_nodes)
        # Expand all items
        self.expand_top_level_nodes()
        self.ui.treeWidget_VideoFiles.resizeColumnToContents(0)
        self.update()


    def expand_top_level_nodes(self):
        for aTopLevelItem in self.top_level_nodes:
            self.ui.treeWidget_VideoFiles.expandItem(aTopLevelItem)


    # Called on .findFilesInSearchDirectoryComplete
    @pyqtSlot(str)
    def on_update_search_path(self, updatedSearchPath):
        if updatedSearchPath not in self.get_video_loader().get_cache().keys():
            print("Error: on_update_search_path(updatedSearchPath: {0}) called but the item didn't exist in the cache!".format(str(updatedSearchPath)))
            return

        cache_value = self.get_video_loader().get_cache()[updatedSearchPath]
        curr_search_path_video_files = cache_value.get_combined_video_files()
        curr_search_path_data_file_map = cache_value.get_combined_video_file_basenames_to_data_file_list_map()
        curr_search_path_output_data_files = []

        # Try to get the relevant node:
        foundTopLevelNode = None
        for aTopLevelItem in self.top_level_nodes:
            itemText = aTopLevelItem.text(0)
            if (itemText != updatedSearchPath):
                # Keep searching
                continue
            else:
                # Found the item to update...
                # aTopLevelItem.setText(int column, const QString &text)

                numChildrenNodes = aTopLevelItem.childCount()
                childrenNodes = aTopLevelItem.takeChildren() # Gets and removes the children nodes
                # aTopLevelItem.child(childIndex)

                for aFoundVideoFile in curr_search_path_video_files:
                    aCurrVideoFileBasename = aFoundVideoFile.get_base_name()

                    potentially_computed_end_date = aFoundVideoFile.get_computed_end_date()
                    if potentially_computed_end_date:
                        computed_end_date = str(potentially_computed_end_date)
                    else:
                        computed_end_date = 'Loading...'

                    aNewVideoNode = QTreeWidgetItem([str(aFoundVideoFile.full_name), str(aFoundVideoFile.parsed_date), computed_end_date, str(aFoundVideoFile.is_deeplabcut_labeled_video)])
                    # aNewVideoNode.setIcon(0,QIcon("your icon path or file name "))
                    aNewVideoNode.setData(0, Qt.UserRole, QVariant(aFoundVideoFile)) # NEW: set the data of the item to the actual found video file object


                    currSource = aFoundVideoFile.get_source()
                    currForeground = MainObjectListsWindow.TreeItem_Default_Foreground
                    currFont = MainObjectListsWindow.TreeItem_Default_Font

                    if currSource == CachedFileSource.OnlyFromDatabase:
                        currForeground = MainObjectListsWindow.TreeItem_DatabaseOnly_Foreground
                        pass
                    elif currSource == CachedFileSource.OnlyFromFilesystem:
                        currForeground = MainObjectListsWindow.TreeItem_FilesystemOnly_Foreground
                        pass
                    elif currSource == CachedFileSource.NewestFromDatabase:
                        currForeground = MainObjectListsWindow.TreeItem_DatabaseNewer_Foreground
                        pass
                    elif currSource == CachedFileSource.NewestFromFilesystem:
                        currForeground = MainObjectListsWindow.TreeItem_FilesystemNewer_Foreground
                        pass
                    elif currSource == CachedFileSource.Identical:
                        currForeground =  MainObjectListsWindow.TreeItem_Default_Foreground
                        pass
                    else:
                        pass

                    aNewVideoNode.setForeground(0, currForeground)
                    aNewVideoNode.setFont(0, currFont)
                    
                    # Check for data files:
                    curr_video_file_output_data_files = []
                    if aCurrVideoFileBasename in curr_search_path_data_file_map.keys():
                        curr_video_file_output_data_files = curr_search_path_data_file_map[aCurrVideoFileBasename]

                    # print("ui loadedVideoFiles[{0}]: {1}".format(str(key_path), len(curr_video_file_output_data_files)))
                    for aFoundDataFile in curr_video_file_output_data_files:
                        aNewDataNode = QTreeWidgetItem([str(aFoundDataFile.full_name), str(aFoundDataFile.parsed_date), computed_end_date, str(aFoundDataFile.get_deeplabcut_info_string())])
                        # aNewDataNode.setData(0, Qt.UserRole, QVariant(aFoundVideoFile))
                        aNewDataNode.setData(0, Qt.UserRole, aFoundDataFile) # Set the user-data of the QTreeWidgetItem to be the actual found data file.

                        # aNewVideoNode.setIcon(0,QIcon("your icon path or file name "))

                        currSource = aFoundDataFile.get_source()
                        currForeground = MainObjectListsWindow.TreeItem_Default_Foreground
                        currFont = MainObjectListsWindow.TreeItem_Default_Font

                        if currSource == CachedFileSource.OnlyFromDatabase:
                            currForeground = MainObjectListsWindow.TreeItem_DatabaseOnly_Foreground
                            pass
                        elif currSource == CachedFileSource.OnlyFromFilesystem:
                            currForeground = MainObjectListsWindow.TreeItem_FilesystemOnly_Foreground
                            pass
                        elif currSource == CachedFileSource.NewestFromDatabase:
                            currForeground = MainObjectListsWindow.TreeItem_DatabaseNewer_Foreground
                            pass
                        elif currSource == CachedFileSource.NewestFromFilesystem:
                            currForeground = MainObjectListsWindow.TreeItem_FilesystemNewer_Foreground
                            pass
                        elif currSource == CachedFileSource.Identical:
                            currForeground =  MainObjectListsWindow.TreeItem_Default_Foreground
                            pass
                        else:
                            pass

                        aNewDataNode.setForeground(0, currForeground)
                        aNewDataNode.setFont(0, currFont)

                        aNewVideoNode.addChild(aNewDataNode)

                    # Add the new video node to the group
                    aTopLevelItem.addChild(aNewVideoNode)

                print("Found matching top-level-node.")
                foundTopLevelNode = aTopLevelItem
                aTopLevelItem.setExpanded(True)
                break


        if foundTopLevelNode is not None:
            # self.ui.treeWidget_VideoFiles.addTopLevelItems(self.top_level_nodes)
            # Expand all items
            self.expand_top_level_nodes()
            self.ui.treeWidget_VideoFiles.resizeColumnToContents(0)
            self.update()
        else:
            print("Failed to find a top-level node matching {0}".format(str(updatedSearchPath)))
            return



    # TODO: update end_date without rebuilding the whole table
    def update_end_date(self, top_level_index, child_index, new_date):
        curr_top_level_node = self.top_level_nodes[top_level_index]
        curr_child_node = curr_top_level_node.child(child_index)
        curr_child_node.setText(2, new_date)



    # Event Handlers:
    def keyPressEvent(self, event):
        pass
        
    def mouseMoveEvent(self, event):
        pass

    def handle_menu_load_event(self):
        print("actionLoad")
        pass

    def handle_menu_save_event(self):
        print("actionSave")
        self.saveVideoFilesToDatabase()
        pass

    def handle_menu_refresh_event(self):
        print("actionRefresh")
        self.reload_data()
        pass

    def handle_add_search_directory_activated(self):
        print("handle_add_search_directory_activated")
        # options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        # # fileName, _ = QtWidgets.QFileDialog.getOpenFileName(
        # #                 None,
        # #                 "QFileDialog.getOpenFileName()",
        # #                 "",
        # #                 "All Files (*);;Python Files (*.py)",
        # #                 options=options)
        # folderName, _ = QFileDialog.getExistingDirectory(
        #                 None,
        #                 "Select Directory containing Video Files")

        # startingDir = cmds.workspace(q=True, rootDirectory=True)
        startingDir = str(Path.home().resolve())
        destDir = QFileDialog.getExistingDirectory(None, 
                                                         'Open working directory', 
                                                         startingDir, 
                                                         QFileDialog.ShowDirsOnly)



        if destDir:
            print("getting folder name: {0}".format(str(destDir)))
            self.videoLoader.add_search_path(destDir)

    def handle_save_selection_action(self):
        print("handle_save_selection_action()")

    def handle_get_conversion_list_action(self):
        print("handle_get_conversion_list_action()")
        unconvertedFiles = dict()
        convertedFiles = dict()

        unconvertedParentPaths = dict()
        convertedParentPaths = dict()

        needs_conversion_files = []
        handbrake_conversion_queue = []

        pairsList = []
        # Find children folders with different roots
        for (key_path, cache_value) in self.get_video_loader().get_cache().items():
            curr_cache_root_anchor = cache_value.get_root_anchor()
            curr_cache_remainder = cache_value.get_non_root_remainder()
            
            for aVideoFile in cache_value.get_combined_video_files():
                currFileExtension = aVideoFile.file_extension[1:].lower()
                if currFileExtension == 'mp4':
                    # Converted
                    convertedFiles[aVideoFile.base_name] = aVideoFile
                    convertedParentPaths[aVideoFile.parent_path] = None
                else:
                    # non-converted
                    unconvertedFiles[aVideoFile.base_name] = aVideoFile
                    unconvertedParentPaths[aVideoFile.parent_path] = None
           
       
        for (aKey_basename, converted_file_value) in convertedFiles.items():
            if (aKey_basename in unconvertedFiles.keys()):
                # Get the converted/unconverted parent paths to set up the bidirectional mapping
                theUnconvertedParentPath = unconvertedFiles[aKey_basename].parent_path
                theConvertedParentPath = converted_file_value.parent_path

                convertedParentPaths[theConvertedParentPath] = theUnconvertedParentPath
                # The item exists in the unconverted array, remove it from it.
                unconvertedParentPaths[theUnconvertedParentPath] = theConvertedParentPath
                # unconvertedFiles[aKey_basename] = None # Remove the key
                del unconvertedFiles[aKey_basename]

        for (anOutputUnconvertedFileKey, anOutputUnconvertedFileValue) in unconvertedFiles.items():
            needs_conversion_files.append(anOutputUnconvertedFileValue.path)

            # get basename
            new_full_name = anOutputUnconvertedFileValue.base_name + '.mp4'

            # Check the converted map to see if the unconverted parent path has an entry we can look up
            theConvertedParentPath = unconvertedParentPaths[anOutputUnconvertedFileValue.parent_path]

            new_full_path = theConvertedParentPath + new_full_name
            ## TODO: working on file conversions

            new_job = HandbrakeConversionQueue(anOutputUnconvertedFileValue.path, new_full_path)

        # print("found matching pairs: {0}".format(str(pairsList)))
        # print("unique unconverted files: {0}".format(str(unconvertedFiles)))
        print("unique unconverted files: {0}".format(str(needs_conversion_files)))
        
        HandbrakeConversionQueue, save_handbrake_conversion_queue

    # @pyqtSlot(int, int)
    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_selection_event(self, trackIndex, trackObjectIndex):
       pass

    # Occurs when the user selects an object in the child video track with the mouse
    def handle_child_hover_event(self, trackIndex, trackObjectIndex):
        pass

    # TODO: Unused. Decided to set the node's data (Qt.UserRole) instead
    # Note: Doesn't work because the deeplabcut files are nested below their video file
    def recover_full_path(self, tree_item):
        accumulated_path = [tree_item.text(0)]
        potentialParent = tree_item.parent()
        while potentialParent is not None:
            accumulated_path.append(potentialParent.text(0))
            potentialParent = potentialParent.parent() # Get the parent's parent
            pass

        else:
            # Otherwise we have the root-most item
            accumulated_path.reverse()
            print(str(accumulated_path))
            pass

        return accumulated_path


    # Generates the menu to be displayed for a point in the tree.
    def menuContextTree(self, point):

        # Infos about the node selected.
        index = self.ui.treeWidget_VideoFiles.indexAt(point)

        if not index.isValid():
            return

        item = self.ui.treeWidget_VideoFiles.itemAt(point)
        name = item.text(0)  # The text of the node.
        # accumulated_array = self.recover_full_path(item)

        # TODO: List items crash on right click, because user_data is NONE
        user_data = item.data(0, Qt.UserRole)
        if user_data is not None:
            active_item_full_path = user_data.get_full_path()
        else:
            print('WARNING, TODO: Item has no user_data, check the assumptions about the item type (I assert that it is a root-path node)')
            # I believe the item's text should be the full path (because now the user data is only None for the "top-level" nodes which indicate the search path)
            active_item_full_path = name

        # print("user_data: {0}".format(str(user_data)))
        # print("user_data: {0}".format(str(active_item_full_path)))

        # We build the (context?) menu.
        menu = QtWidgets.QMenu()
        # action = menu.addAction("Open item")
        # action = menu.addAction(name)

        # See if it's a .csv, .h5, or .pickle file:
        active_item_path = Path(active_item_full_path)
        found_extension = active_item_path.suffix
        print("found_extension: {0}".format(str(found_extension)))
        found_output_format = DeeplabCutOutputFileType.get_from_extension(found_extension)
        if found_output_format is not None:
            # Specifically a deeplabcut output file
            load_file_action = menu.addAction("Load DeeplabCut output file...")
            output_event_file = DeeplabcutEventFile(active_item_path, found_output_format, parent=self)

            load_file_action.setData(output_event_file)
            # action = menu.addAction(name)
            # load_file_action.triggered.connect(self.on_click_deeplabcut_file_menu_action_load)
            menu.triggered.connect(self.on_click_deeplabcut_file_menu_action_load)

            # 


        else:
            # Non DLC output file extension type
            menu.addSeparator()
            action_1 = menu.addAction("Option 1")
            action_2 = menu.addAction("Option 2")
            action_3 = menu.addAction("Option 3")


        menu.exec_(self.ui.treeWidget_VideoFiles.mapToGlobal(point))



    def refresh_child_widget_display(self):
        pass


    @pyqtSlot(str, DeeplabCutOutputFileType)
    def load_deeplabcut_data_file(self, file_path, output_file_type):
        output_event_file = DeeplabcutEventFile(file_path, output_file_type, parent=self)
        output_event_file.dataReloaded.connect(self.on_data_reloaded)
        output_event_file.load_data()



    @pyqtSlot(pd.DataFrame)
    def on_data_reloaded(self, df):
        print("on_data_reloaded(df: {0})".format(str(df)))
        frame_column_names = df.columns.names
        frame_column_levels = df.columns.levels

        dlc_command_info = df.columns.levels[0].values[0] # 'DLC_resnet50_ReachingSep27shuffle1_1030000'
        body_parts_list = list(df.columns.levels[1].values) # ['earL' 'earR' 'nose' 'tail1' 'tailbase']
        value_index_names = df.columns.levels[2].values # ['likelihood' 'x' 'y']

        newModel = PandasTableModel(df, dlc_command_info)
        self.currentTablePreviewWidget = PandasTableWidget([newModel], parent=None)
        self.currentTablePreviewWidget.show()


    @pyqtSlot(QtWidgets.QAction)
    def on_click_deeplabcut_file_menu_action_load(self, action):
        print("on_click_deeplabcut_file_menu_action_load(action: {0})".format(action.text()))
        menu_action_name = action.text()
        menu_action_data = action.data()
        if menu_action_data is not None:
            print("Found valid action: {0}".format(str(menu_action_name)))
            menu_action_data.dataReloaded.connect(self.on_data_reloaded)
            menu_action_data.load_data()

        # self.load_deeplabcut_data_file()
        # print('Action: ', action.text())
    

    
