#Filters.py
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal

"""
Represents a filter for a specific track
"""
class TrackFilter(QObject):
    def __init__(self, behavioral_box_id, experiment_id, cohort_id, animal_id, parent=None):
        super(TrackFilter, self).__init__(parent=parent)
        self.behavioral_box_id = behavioral_box_id
        self.experiment_id = experiment_id
        self.cohort_id = cohort_id
        self.animal_id = animal_id


    def __str__(self):
        return 'TrackFilter: behavioral_box_id: {0}, experiment_id: {1}, cohort_id: {2}, animal_id: {3}'.format(self.behavioral_box_id, self.experiment_id, self.cohort_id, self.animal_id)

    def get_output_dict(self):
        return {'behavioral_box_id': self.behavioral_box_id, 'experiment_id': self.experiment_id, 'cohort_id': self.cohort_id, 'animal_id': self.animal_id}
