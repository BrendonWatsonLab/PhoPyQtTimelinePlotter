import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

# from app.BehaviorsList import BehaviorsManager, BehaviorInfoOptions
# from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef
# from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors

# from GUI.UI.DialogComponents.DialogComponents_StartEndDate

# from GUI.UI.DialogComponents.DialogComponents_BoxExperCohortAnimalIDs import DialogComponents_BoxExperCohortAnimalIDs

class DialogComponents_BoxExperCohortAnimalIDs(QFrame):

    def __init__(self, parent=None):
        super(DialogComponents_BoxExperCohortAnimalIDs, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/DialogComponents/BoxExperCohortAnimalIDs_DialogComponents.ui", self) # Load the .ui file
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        self.ui.spinBox_bbID.valueChanged[int].connect(self.on_bb_id_value_changed)
        self.ui.spinBox_experimentID.valueChanged[int].connect(self.on_experiment_id_value_changed)
        self.ui.spinBox_cohortID.valueChanged[int].connect(self.on_cohort_id_value_changed)
        self.ui.spinBox_animalID.valueChanged[int].connect(self.on_animal_id_value_changed)

        # self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)
        # self.ui.comboBox_Subtype.activated[str].connect(self.on_subtype_combobox_changed)
        self.update_conditional_highlighting()
        pass

    

    @pyqtSlot(int)
    def on_bb_id_value_changed(self, val):
        print('on_bb_id_value_changed changed: {0}'.format(val))
        self.ui.lblBBID.setEnabled(val > 0)
        return

    @pyqtSlot(int)
    def on_experiment_id_value_changed(self, val):
        print('on_experiment_id_value_changed changed: {0}'.format(val))
        self.ui.lblExperimentID.setEnabled(val > 0)
        return

    @pyqtSlot(int)
    def on_cohort_id_value_changed(self, val):
        print('on_cohort_id_value_changed changed: {0}'.format(val))
        self.ui.lblCohortID.setEnabled(val > 0)
        return

    @pyqtSlot(int)
    def on_animal_id_value_changed(self, val):
        print('on_animal_id_value_changed changed: {0}'.format(val))
        self.ui.lblAnimalID.setEnabled(val > 0)
        return


    def update_conditional_highlighting(self):
        # update_conditional_highlighting(...): enables/disables the labels to demonstrate which indicies are valid for each field
        self.ui.lblBBID.setEnabled(self.ui.spinBox_bbID.value() > 0)
        self.ui.lblExperimentID.setEnabled(self.ui.spinBox_experimentID.value() > 0)
        self.ui.lblCohortID.setEnabled(self.ui.spinBox_cohortID.value() > 0)
        self.ui.lblAnimalID.setEnabled(self.ui.spinBox_animalID.value() > 0)

    def get_id_values(self):
        v1 = self.ui.spinBox_bbID.value()
        v2 = self.ui.spinBox_experimentID.value()
        v3 = self.ui.spinBox_cohortID.value()
        v4 = self.ui.spinBox_animalID.value()

        if (v1 < 1):
            v1 = None
        if (v2 < 1):
            v2 = None
        if (v3 < 1):
            v3 = None
        if (v4 < 1):
            v4 = None
        
        return (v1, v2, v3, v4)

    def set_id_values(self, behavioral_box_id, experiment_id, cohort_id, animal_id):
        if behavioral_box_id is None:
            self.ui.spinBox_bbID.setValue(0)
        else:
            self.ui.spinBox_bbID.setValue(behavioral_box_id)

        if experiment_id is None:
            self.ui.spinBox_experimentID.setValue(0)
        else:
            self.ui.spinBox_experimentID.setValue(experiment_id)

        if cohort_id is None:
            self.ui.spinBox_cohortID.setValue(0)
        else:
            self.ui.spinBox_cohortID.setValue(cohort_id)

        if animal_id is None:
            self.ui.spinBox_animalID.setValue(0)
        else:
            self.ui.spinBox_animalID.setValue(animal_id)

        self.update_conditional_highlighting()
        self.update()
        return

    
    def set_editable(self, is_editable):
        for aControl in [self.ui.spinBox_bbID, self.ui.spinBox_experimentID, self.ui.spinBox_cohortID, self.ui.spinBox_animalID]:
            aControl.setReadOnly(not is_editable)