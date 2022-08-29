# UIState.py
import sys
from enum import Enum

# from datetime import datetime, timezone, timedelta
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt5.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
)

# import GUI.UI.UIState as UIState
# from phopyqttimelineplotter.GUI.UI.UIState import ItemInteractionState, ItemHoverState, ItemSelectionState


class ItemHoverState(Enum):
    Deemphasized = 1  # Deemphasized
    Default = 2  # Default
    Emphasized = 3  #  Emphasized

    def is_emphasized(self):
        if self == ItemHoverState.Emphasized:
            return True
        else:
            return False

    def is_deemphasized(self):
        if self == ItemHoverState.Deemphasized:
            return True
        else:
            return False


class ItemSelectionState(Enum):
    Default = 1  # Default
    PartiallySelected = 2  # PartiallySelected
    Selected = 3  #  Selected

    def is_selected(self):
        if self == ItemSelectionState.Default:
            return False
        else:
            return True

    def is_fully_selected(self):
        if self == ItemSelectionState.Selected:
            return True
        else:
            return False

    def is_partially_selected(self):
        if self == ItemSelectionState.PartiallySelected:
            return True
        else:
            return False


class ItemInteractionState(QObject):
    def __init__(
        self,
        hoverState=ItemHoverState.Default,
        selectionState=ItemSelectionState.Default,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.hoverState = hoverState
        self.selectionState = selectionState

    ## Hover:
    def is_emphasized(self):
        return self.hoverState.is_emphasized()
        # if self.hoverState == ItemHoverState.Emphasized:
        #     return True
        # else:
        #     return False

    def is_deemphasized(self):
        return self.hoverState.is_deemphasized()

    def get_hover_state(self):
        return self.hoverState

    def set_hover_state(self, newState):
        self.hoverState = newState

    ## Selection:
    def get_selection_state(self):
        return self.selectionState

    def set_selection_state(self, newState):
        self.selectionState = newState

    def is_selected(self):
        return self.selectionState.is_selected()
