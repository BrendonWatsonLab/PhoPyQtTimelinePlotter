import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QDialog
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

from GUI.UI.DialogComponents.AbstractDialogMixins import BoxExperCohortAnimalIDsFrame_Mixin

class VideoTrackFilterEditDialog(BoxExperCohortAnimalIDsFrame_Mixin, QDialog):

     # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal()

     # This defines a signal called 'closed' that takes no arguments.
    on_commit = pyqtSignal(int, str, int, int, int, int, bool, bool)

    def __init__(self, trackConfig, parent=None):
        super(VideoTrackFilterEditDialog, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.trackConfig = trackConfig
        # self.ui = uic.loadUi("GUI/UI/VideoTrackFilterEditWidget/VideoTrackFilterEditWidget.ui", self) # Load the .ui file
        self.ui = uic.loadUi("GUI/UI/VideoTrackFilterEditWidget/VideoTrackFilterEditDialog.ui", self) # Load the .ui file

        self.enable_none_selection = True # if true, an "empty" item is added to the combobox dropdown lists which is selected by default
        self.reloadModelFromConfig()
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):

        # self.ui.lblTrackID.setText("TestTrackID")
        # self.ui.lblTrackName.setText("TestTrackName")
        # self.ui.checkBox_isOriginalVideo

        # self.ui.frame_BoxExperCohortAnimalIDs

        # self.ui.frame_BoxExperCohortAnimalIDs
        # self.ui.Frame_BoxExperCohorAnimalID
        return

    ## Data Model Functions:
    # Updates the member variables from the track config
    def reloadModelFromConfig(self):
        self.ui.lblTrackID.setText(str(self.trackConfig.get_track_id()))
        self.ui.lblTrackName.setText(self.trackConfig.get_track_title())

        currTrackFilter = self.trackConfig.filter
        behavioral_box_id, experiment_id, cohort_id, animal_id = 0, 0, 0, 0
        if currTrackFilter.behavioral_box_ids is not None:
            behavioral_box_id = currTrackFilter.behavioral_box_ids[0] 
        if currTrackFilter.experiment_ids is not None:
            experiment_id = currTrackFilter.experiment_ids[0]            
        if currTrackFilter.cohort_ids is not None:
            cohort_id = currTrackFilter.cohort_ids[0]            
        if currTrackFilter.animal_ids is not None:
            animal_id = currTrackFilter.animal_ids[0]            

        self.set_is_original_video(currTrackFilter.allow_original_videos)
        self.set_is_tagged_video(currTrackFilter.allow_labeled_videos)
        
        self.set_id_values(behavioral_box_id, experiment_id, cohort_id, animal_id)

    def accept(self):
        print('accept:')
        # Emit the signal.
        behavioral_box_id, experiment_id, cohort_id, animal_id = self.get_id_values()
        final_bb_id, final_experiment_id, final_cohort_id, final_animal_id = int(behavioral_box_id or -1), int(experiment_id or -1), int(cohort_id or -1), int(animal_id or -1)
        self.on_commit.emit(int(self.get_trackID()), self.get_trackName(), final_bb_id, final_experiment_id, final_cohort_id,
            final_animal_id, self.get_is_original_video(), self.get_is_tagged_video())
        super(VideoTrackFilterEditDialog, self).accept()

    def reject(self):
        print('reject:')
        self.on_cancel.emit()
        super(VideoTrackFilterEditDialog, self).reject()

    
    def get_trackID(self):
        return self.ui.lblTrackID.text()
    
    def get_trackName(self):
        return self.ui.lblTrackName.text()

    def set_trackID(self, updatedStr):
        self.ui.lblTrackID.setText(updatedStr)

    def set_trackName(self, updatedStr):
        self.ui.lblTrackName.setText(updatedStr)

    def get_is_original_video(self):
        return self.ui.checkBox_isOriginalVideo.isChecked()

    def set_is_original_video(self, is_original):
        self.ui.checkBox_isOriginalVideo.setChecked(is_original)


    def get_is_tagged_video(self):
        return self.ui.checkBox_isTaggedVideo.isChecked()

    def set_is_tagged_video(self, is_tagged):
        self.ui.checkBox_isTaggedVideo.setChecked(is_tagged)


        