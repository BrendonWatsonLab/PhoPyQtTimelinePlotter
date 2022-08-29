# CustomDataSelectionWidget.py
# Generated from c:\Users\pho\repos\PhoPyQtTimelinePlotter\src\phopyqttimelineplotter\GUI\UI\CustomDataSelectionWidget\CustomDataSelectionWidget.ui automatically by PhoPyQtClassGenerator VSCode Extension
import sys
from PyQt6 import QtCore, QtGui, QtWidgets

## IMPORTS:
# from GUI.UI.CustomDataSelectionWidget import CustomDataSelectionWidget
from phopyqttimelineplotter.GUI.UI.CustomDataSelectionWidget.Uic_AUTOGEN_CustomDataSelectionWidget import Ui_CustomDataSelectionWidget

from pathlib import Path
# C:\Users\pho\repos\PhoPyQtTimelinePlotter\app
from phopyqttimelineplotter.app.filesystem.FilesystemRecordBase import discover_data_files
# from app.filesystem.FilesystemRecordBase import discover_data_files

# silx GUI:
from silx.gui import qt
from silx.gui.plot.StackView import StackViewMainWindow

from silx.gui.dialog.GroupDialog import GroupDialog

class CustomDataSelectionWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent) # Call the inherited classes __init__ method
        # self.ui = uic.loadUi("GUI/UI/CustomDataSelectionWidget/CustomDataSelectionWidget.ui", self) # Load the .ui file
        self.ui = Ui_CustomDataSelectionWidget()
        self.ui.setupUi(self) # builds the design from the .ui onto this widget.
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        # wants_recurrsive_data_file_search = False
        wants_recurrsive_data_file_search = True
        # files_search_parent_path = Path(r'R:\data\RoyMaze1')
        # files_search_parent_path = Path(r'W:\Data\KDIBA\gor01\one\2006-6-08_14-26-15')
        files_search_parent_path = Path(r'C:\Users\pho\repos\PhoPy3DPositionAnalysis2021')
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


        self.ui.toolButton.clicked.connect(self.on_click_select_group_button)
        self.ui.lineEdit.setText("")

    def __str__(self):
         return 

    def on_click_select_group_button(self):
        dialog = GroupDialog()
        # dialog.addFile(str(filenames_list[0]))
        [dialog.addFile(str(a_filename)) for a_filename in self.filenames_list]
        dialog.show()
        if dialog.exec():
            selected_timestamp_data_url = dialog.getSelectedDataUrl()
            print("File path: %s" % selected_timestamp_data_url.file_path())
            print("HDF5 group path : %s " % selected_timestamp_data_url.data_path())
            self.ui.lineEdit.setText(f'{selected_timestamp_data_url.data_path()}')

        else:
            print("Operation cancelled :(")



## Start Qt event loop
if __name__ == '__main__':
    import pyqtgraph as pg
    app = pg.mkQApp("CustomDataSelectionWidget Example")
    widget = CustomDataSelectionWidget()
    widget.show()
    pg.exec()
    