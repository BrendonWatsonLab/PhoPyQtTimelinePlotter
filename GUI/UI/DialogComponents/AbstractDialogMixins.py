# AbstractDialogMixins.py
import sys
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize

# INCLUDE:
# from GUI.UI.DialogComponents.AbstractDialogMixins import *

""" DialogObjectIdentifier:
Holds the trackID and childID that a given dialog refers to
"""
class DialogObjectIdentifier(QObject):
    def __init__(self, trackID, childID, parent=None):
        super(DialogObjectIdentifier, self).__init__(parent=parent)
        self._trackID = trackID
        self._childID = childID

    @property
    def trackID(self):
        return self._trackID

    @property
    def childID(self):
        return self._childID

    # Setters:
    @trackID.setter
    def trackID(self, new_value):
        if self._trackID != new_value:
            self._trackID = new_value
        else:
            # Otherwise nothing has changed
            pass

    @childID.setter
    def childID(self, new_value):
        if self._childID != new_value:
            self._childID = new_value
        else:
            # Otherwise nothing has changed
            pass

    def __eq__(self, otherIdentifier):
        return self._trackID == otherIdentifier._trackID and self._childID == otherIdentifier._childID




# requires self.referredObjectID exists    
class ObjectSpecificDialogMixin(object):

    def get_referred_object_identifier(self):
        return self.referredObjectID

    def set_referred_object_identifiers(self, trackID, childEventID):
        self.referredObjectID = DialogObjectIdentifier(trackID, childEventID)

class BoxExperCohortAnimalIDsFrame_Mixin(object):
    # @method_decorator(network_protected)

    # requires a property "self.ui.frame_BoxExperCohortAnimalIDs"

    # @property
    def get_id_values(self, shouldReturnNoneTypes=True):
        return self.ui.frame_BoxExperCohortAnimalIDs.get_id_values(shouldReturnNoneTypes)

    # @property
    def set_id_values(self, behavioral_box_id, experiment_id, cohort_id, animal_id):
        self.ui.frame_BoxExperCohortAnimalIDs.set_id_values(behavioral_box_id, experiment_id, cohort_id, animal_id)

    # @property
    def set_id_frame_editability(self, is_editable):
        self.ui.frame_BoxExperCohortAnimalIDs.set_editable(is_editable)