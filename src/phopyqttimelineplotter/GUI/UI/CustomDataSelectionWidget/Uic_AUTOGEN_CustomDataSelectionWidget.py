# Form implementation generated from reading ui file 'c:\Users\pho\repos\PhoPyQtTimelinePlotter\src\phopyqttimelineplotter\GUI\UI\CustomDataSelectionWidget\CustomDataSelectionWidget.ui'
#
# Created by: PyQt6 UI code generator 6.3.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


# from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CustomDataSelectionWidget(object):
    def setupUi(self, customDataSelectionWidget):
        customDataSelectionWidget.setObjectName("CustomDataSelectionWidget")
        customDataSelectionWidget.resize(424, 300)
        self.formLayout = QtWidgets.QFormLayout(customDataSelectionWidget)
        self.formLayout.setObjectName("formLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(customDataSelectionWidget)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(customDataSelectionWidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit.sizePolicy().hasHeightForWidth())
        self.lineEdit.setSizePolicy(sizePolicy)
        self.lineEdit.setMinimumSize(QtCore.QSize(100, 0))
        self.lineEdit.setBaseSize(QtCore.QSize(100, 0))
        self.lineEdit.setToolTip("")
        self.lineEdit.setInputMask("")
        self.lineEdit.setText("")
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout_2.addWidget(self.lineEdit)
        self.toolButton = QtWidgets.QToolButton(customDataSelectionWidget)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout_2.addWidget(self.toolButton)
        self.horizontalLayout_2.setStretch(1, 1)
        self.formLayout.setLayout(
            0, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.horizontalLayout_2
        )
        self.widget = CustomDataSelectionWidget_Subpanel_SimpleXY(
            customDataSelectionWidget
        )
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QtCore.QSize(400, 79))
        self.widget.setBaseSize(QtCore.QSize(400, 79))
        self.widget.setObjectName("widget")
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.widget
        )

        self.retranslateUi(customDataSelectionWidget)
        QtCore.QMetaObject.connectSlotsByName(customDataSelectionWidget)

    def retranslateUi(self, CustomDataSelectionWidget):
        _translate = QtCore.QCoreApplication.translate
        CustomDataSelectionWidget.setWindowTitle(
            _translate("CustomDataSelectionWidget", "CustomDataSelectionWidget")
        )
        self.label.setText(_translate("CustomDataSelectionWidget", "timestamps"))
        self.toolButton.setText(_translate("CustomDataSelectionWidget", "..."))


from phopyqttimelineplotter.GUI.UI.CustomDataSelectionWidget.CustomDataSelectionWidget_Subpanel_SimpleXY import (
    CustomDataSelectionWidget_Subpanel_SimpleXY,
)
