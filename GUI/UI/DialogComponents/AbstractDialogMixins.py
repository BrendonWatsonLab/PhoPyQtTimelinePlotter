# AbstractDialogMixins.py
import sys

# INCLUDE:
# from GUI.UI.DialogComponents.AbstractDialogMixins import *


class BoxExperCohortAnimalIDsFrame_Mixin(object):
    # @method_decorator(network_protected)

    # requires a property "self.ui.frame_BoxExperCohortAnimalIDs"

    # @property
    def get_id_values(self):
        return self.ui.frame_BoxExperCohortAnimalIDs.get_id_values()

    # @property
    def set_id_values(self, behavioral_box_id, experiment_id, cohort_id, animal_id):
        self.ui.frame_BoxExperCohortAnimalIDs.set_id_values(behavioral_box_id, experiment_id, cohort_id, animal_id)

    # @property
    def set_id_frame_editability(self, is_editable):
        self.ui.frame_BoxExperCohortAnimalIDs.set_editable(is_editable)