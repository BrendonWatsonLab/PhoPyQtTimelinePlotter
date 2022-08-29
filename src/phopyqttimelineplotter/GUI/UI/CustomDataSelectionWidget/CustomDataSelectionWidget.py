# CustomDataSelectionWidget.py
# Generated from c:\Users\pho\repos\PhoPyQtTimelinePlotter\src\phopyqttimelineplotter\GUI\UI\CustomDataSelectionWidget\CustomDataSelectionWidget.ui automatically by PhoPyQtClassGenerator VSCode Extension
import sys
from pathlib import Path

# silx GUI:
import silx.io

# from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt5 import QtCore, QtGui, QtWidgets
from silx.gui import qt
from silx.gui.dialog.GroupDialog import GroupDialog
from silx.gui.widgets.ThreadPoolPushButton import (
    ThreadPoolPushButton,  # alternative: WaitingPushButton
)
from silx.io.url import DataUrl # DataUrl
from silx.io.utils import H5Type, get_h5_class, get_h5py_class  # not sure which to use

# C:\Users\pho\repos\PhoPyQtTimelinePlotter\app
from phopyqttimelineplotter.app.filesystem.FilesystemRecordBase import (
    discover_data_files,
)

## IMPORTS:
# from phopyqttimelineplotter.GUI.UI.CustomDataSelectionWidget import CustomDataSelectionWidget
from phopyqttimelineplotter.GUI.UI.CustomDataSelectionWidget.Uic_AUTOGEN_CustomDataSelectionWidget import (
    Ui_CustomDataSelectionWidget,
)

# from silx.gui.plot.StackView import StackViewMainWindow


# from phopyqttimelineplotter.app.filesystem.FilesystemRecordBase import discover_data_files


class CustomDataSelectionWidget(qt.QWidget):
    
    loadDataSelection = qt.pyqtSignal(object) # a dictionary
    
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)  # Call the inherited classes __init__ method
        ## Setup Variables
        # self._selected_data = dict() # a dictionary with keys == variable name, and values == variable url
        self._selected_data = dict(
            t=None, x=None, y=None
        )  # a dictionary with keys == variable name, and values == DataUrl

        # self.ui = uic.loadUi("GUI/UI/CustomDataSelectionWidget/CustomDataSelectionWidget.ui", self) # Load the .ui file
        self.ui = Ui_CustomDataSelectionWidget()
        self.ui.setupUi(self)  # builds the design from the .ui onto this widget.
        self.initUI()
        self.show()  # Show the GUI

    def initUI(self):
        # wants_recurrsive_data_file_search = False
        wants_recurrsive_data_file_search = True
        # files_search_parent_path = Path(r'R:\data\RoyMaze1')
        # files_search_parent_path = Path(r'W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15')
        files_search_parent_path = Path(
            r"C:\Users\pho\repos\PhoPy3DPositionAnalysis2021"
        )
        ## Dynamic from files_search_parent_path:
        # self.filenames_list = discover_data_files(files_search_parent_path, file_extension='.h5', recursive=wants_recurrsive_data_file_search)

        ## Hardcoded .mat files:
        filenames_strs_list = [
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15-gam.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15-low.mat",
            r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15-replay.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15-rip.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15-ripV6.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.eegseg.mat",
            r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.epochs_info.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.Gamma.mat",
            r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.laps_info.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.NeuronQuality.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.NQv6.mat",
            r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.position_info.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.Rise.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.session.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.spikeII.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.spikeJ.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.spikes.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.SynchCA.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.SynchCA1.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15.SynchCA3.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15HCCG.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15INCCG.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\2006-6-08_14-26-15vt.mat",
            # r"W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15\data_NeuroScope2.mat"
        ]
        self.filenames_list = [Path(filename) for filename in filenames_strs_list]

        self.ui.select_group_dialog = None

        ## Add submission buttons:
        # button = ThreadPoolPushButton(text="Load from paths")
        # button.setCallable(math.pow, 2, 16)
        # button.succeeded.connect(print) # python3
        # self.ui.btnFinalizeLoad.setCallable(self.on_click_finalize_load, self.selected_data)
        self.ui.btnFinalizeLoad.setCallable(self.on_click_finalize_load, self.selected_data_nodes)
        self.ui.btnFinalizeLoad.succeeded.connect(self.on_complete_finalized_load)

        # Setup timestamps field:
        self.ui.toolButton.clicked.connect(
            lambda is_checked, v_name="t": self.on_click_select_group_button(
                is_checked, variable_name=v_name
            )
        )
        self.ui.lineEdit.setText("")

        # Setup x/y widget:

        # x:
        # self.ui.widget.ui.toolButton.clicked.connect(self.on_click_select_group_button)
        self.ui.widget.ui.toolButton.clicked.connect(
            lambda is_checked, v_name="x": self.on_click_select_group_button(
                is_checked, variable_name=v_name
            )
        )
        self.ui.widget.ui.lineEdit.setText("")

        # y:
        # self.ui.widget.ui.toolButton_2.clicked.connect(self.on_click_select_group_button)
        self.ui.widget.ui.toolButton_2.clicked.connect(
            lambda is_checked, v_name="y": self.on_click_select_group_button(
                is_checked, variable_name=v_name
            )
        )
        self.ui.widget.ui.lineEdit_2.setText("")

    @property
    def selected_data_nodes(self):
        """The selected_data_nodes property."""
        return self._selected_data
    @selected_data_nodes.setter
    def selected_data_nodes(self, value):
        self._selected_data = value
        
    @property
    def selected_data_urls(self):
        """The selected_data_urls property."""
        # return {var_name:GroupDialog.selectedUrlFromNode(self.selected_data_nodes.get(var_name, None), subgroupName='') for var_name in list(self.selected_data_nodes.keys())}
        return {var_name:GroupDialog.selectedUrlFromNode(node, subgroupName='') for var_name, node in self.selected_data_nodes.items()}
        
        
    @property
    def selected_data(self):
        """The selected_data property."""
        return self._selected_data
    @selected_data.setter
    def selected_data(self, value):
        self._selected_data = value

    @property
    def are_all_variables_valid(self):
        """The are_all_variables_valid property."""
        set_variables_dict = { a_var_name: a_data_url for a_var_name, a_data_url in self.selected_data_urls.items() if a_data_url is not None }
        valid_only_variables_dict = { a_var_name: a_data_url for a_var_name, a_data_url in set_variables_dict.items() if a_data_url.is_valid() }
        are_all_valid = len(valid_only_variables_dict) == len(self.selected_data_urls)
        return are_all_valid

    def on_click_select_group_button(self, *args, variable_name=None):
        print( f"on_click_select_group_button(*args: {args}, variable_name: {variable_name})" )
        # print(f"self is QWidget: {isinstance(self, QtWidgets.QWidget)}")
        self.ui.select_group_dialog = GroupDialog(parent=self, allowed_selection_types=[H5Type.DATASET, H5Type.GROUP, H5Type.FILE])
        # self.ui.select_group_dialog = GroupDialog()
        # dialog.addFile(str(filenames_list[0]))
        [
            self.ui.select_group_dialog.addFile(str(a_filename))
            for a_filename in self.filenames_list
        ]
        self.ui.select_group_dialog.show()
        if self.ui.select_group_dialog.exec():
            selected_data_node_item = self.ui.select_group_dialog.getSelectedDataNode()
            print(f"selected_data_node_item: {selected_data_node_item}")
            self.on_update_variable(variable_name=variable_name, value=selected_data_node_item)            
            # _selectedUrl = GroupDialog.selectedUrlFromNode(self._selectedNode, subgroupName=self._lineEditNewItem.text())

            # URL object mode:
            selected_timestamp_data_url = (
                self.ui.select_group_dialog.getSelectedDataUrl()
            )
            print(f"selected_timestamp_data_url: {selected_timestamp_data_url}")
            print("File path: %s" % selected_timestamp_data_url.file_path())
            print("HDF5 group path : %s " % selected_timestamp_data_url.data_path())
            self.on_update_variable(variable_name=variable_name, value=selected_timestamp_data_url)
        else:
            print("Operation cancelled :(")

    def on_update_variable(self, variable_name, value):
        """
        value: DataUrl - selected_timestamp_data_url
        value: now a silx.gui.hdf5._utils.H5Node
        """
        self._selected_data[variable_name] = value

        selected_timestamp_data_url = GroupDialog.selectedUrlFromNode(value, subgroupName='')
        sanitized_path = str(selected_timestamp_data_url.data_path())
        # sanitized_path = str(value.data_path())
        lineEdit = self._get_variable_lineEdit(variable_name=variable_name)
        lineEdit.setText(sanitized_path)

        self.ui.btnFinalizeLoad.setEnabled(self.are_all_variables_valid)  # only enable the button if all are valid

    def _get_variable_lineEdit(self, variable_name):
        """returns the lineEdit control for the named variable"""
        if variable_name == "t":
            return self.ui.lineEdit
        elif variable_name == "x":
            return self.ui.widget.ui.lineEdit
        elif variable_name == "y":
            return self.ui.widget.ui.lineEdit_2
        else:
            raise NotImplementedError

    def on_click_finalize_load(self, finalized_selected_data_dict):
        print(f"on_click_finalize_load(selected_data: {finalized_selected_data_dict})")
        self.loadDataSelection.emit(finalized_selected_data_dict) # emit the signal

    def on_complete_finalized_load(self):
        print(f"on_complete_finalized_load")


    @classmethod
    def perform_load_data(cls, finalized_selected_data_dict, limitedVariablesToCreateEventsFor=None):
        """ actually loads the data """
        if limitedVariablesToCreateEventsFor is not None:
            active_variable_names = limitedVariablesToCreateEventsFor

        else:
            # Otherwise load for all variables
            active_variable_names = list(finalized_selected_data_dict.keys())
            
        numVariables = len(active_variable_names)
        activeLoadedDataValuesDict = {var_name:None for var_name in active_variable_names}

        for variableIndex in range(0, numVariables):
            currVariableName = active_variable_names[variableIndex]
            currVariableDataUrl = finalized_selected_data_dict[currVariableName]
            assert currVariableDataUrl is not None
            assert isinstance(currVariableDataUrl, DataUrl)
            
            ## Here we actually load the values:
            currVariableDataValues = silx.io.get_data(currVariableDataUrl)
            activeLoadedDataValuesDict[currVariableName] = currVariableDataValues
        
        return activeLoadedDataValuesDict
    
    
            
## Start Qt event loop
if __name__ == "__main__":
    # import pyqtgraph as pg
    # app = QtWidgets.QApplication([])
    app = qt.QApplication([])
    widget = CustomDataSelectionWidget()
    widget.show()

    result = app.exec()
    # remove ending warnings relative to QTimer
    # app.deleteLater()
    sys.exit(result)

    # app = pg.mkQApp("CustomDataSelectionWidget Example")
    # pg.exec()
