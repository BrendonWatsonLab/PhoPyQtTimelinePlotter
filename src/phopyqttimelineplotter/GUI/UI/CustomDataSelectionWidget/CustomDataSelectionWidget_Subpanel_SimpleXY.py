# CustomDataSelectionWidget_Subpanel_SimpleXY.py
# Generated from c:\Users\pho\repos\PhoPyQtTimelinePlotter\src\phopyqttimelineplotter\GUI\UI\CustomDataSelectionWidget\CustomDataSelectionWidget_Subpanel_SimpleXY.ui automatically by PhoPyQtClassGenerator VSCode Extension

# from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt5 import QtCore, QtGui, QtWidgets

##from phopyqttimelineplotter.GUI.
# from GUI.UI.CustomDataSelectionWidget import CustomDataSelectionWidget_Subpanel_SimpleXY
from phopyqttimelineplotter.GUI.UI.CustomDataSelectionWidget.Uic_AUTOGEN_CustomDataSelectionWidget_Subpanel_SimpleXY import (
    Ui_CustomDataSelectionWidget_Subpanel_SimpleXY,
)


class CustomDataSelectionWidget_Subpanel_SimpleXY(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)  # Call the inherited classes __init__ method
        # self.ui = uic.loadUi("GUI/UI/CustomDataSelectionWidget/CustomDataSelectionWidget_Subpanel_SimpleXY.ui", self) # Load the .ui file

        self.ui = Ui_CustomDataSelectionWidget_Subpanel_SimpleXY()
        self.ui.setupUi(self)  # builds the design from the .ui onto this widget.

        self.initUI()
        self.show()  # Show the GUI

    def initUI(self):
        pass

    def __str__(self):
        return
