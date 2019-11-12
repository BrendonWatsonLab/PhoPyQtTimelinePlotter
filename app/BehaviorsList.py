import sys
from datetime import datetime, timezone, timedelta
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog
# from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QStandardItemModel
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize


class BehaviorInfoOptions(QObject):

    def __init__(self, name='', description='', type=-1, subtype=-1, color=Qt.red, extended_data=dict()):
            super(BehaviorInfoOptions, self).__init__(None)
            self.name = name
            self.description = description
            self.type = type
            self.subtype = subtype
            self.color = color
            self.extended_data = extended_data

class BehaviorNode(QObject):

    def __init__(self, behaviorName, color, parentNode=None, childrenNodes=[]):
        super(BehaviorNode, self).__init__(None)
        self.name = behaviorName
        self.color = color
        self.parentNode = parentNode
        self.childrenNodes = childrenNodes
        self.childrenNodesNameDict = dict()
        for aChildNode in self.childrenNodes:
            self.childrenNodesNameDict[aChildNode.name] = aChildNode

    def add_child(self, childNode):
        if childNode:
            self.childrenNodes.append(childNode)
            self.childrenNodesNameDict[childNode.name] = childNode

    def find_child(self, childName):
        if self.childrenNodesNameDict[childName]:
            return self.childrenNodesNameDict[childName]
        else:
            print("Couldn't find node with name: ", childName)
            return None


class BehaviorsManager(QObject):

    BEHAVIOR_COL, INFO_COL, COLOR_COL = range(3)

    def __init__(self):
        super(BehaviorsManager, self).__init__(None)
        # Color Map:
        self.color_dictionary = dict(zip(BehaviorsManager.get_behaviors_list(), BehaviorsManager.get_behaviors_colors()))
        self.groups_color_dictionary = dict(zip(BehaviorsManager.get_behaviors_group_names_list(), BehaviorsManager.get_behaviors_colors()))
        self.leaf_to_behavior_groups_dict = dict(zip(BehaviorsManager.get_behaviors_list(), BehaviorsManager.get_behaviors_group_names_list()))

        self.uniqueBehaviors = list(set(BehaviorsManager.get_behaviors_list()))
        self.uniqueBehaviorGroups = list(set(BehaviorsManager.get_behaviors_group_names_list()))
        self.uniqueActivityGroups = list(set(BehaviorsManager.get_behaviors_activity_groups_list()))

        self.uniqueBehaviors.sort(reverse = False)
        self.uniqueBehaviorGroups.sort(reverse = False)
        self.uniqueActivityGroups.sort(reverse = False)


    def buildBehaviorsTree(self):
        newRootNode = BehaviorNode('Root', Qt.black, parentNode=None, childrenNodes=[])
        # Add the top-level parent nodes
        for aUniqueBehavior in self.uniqueBehaviorGroups:
            aNewNode = BehaviorNode(aUniqueBehavior, self.groups_color_dictionary[aUniqueBehavior], newRootNode)
            newRootNode.add_child(aNewNode)

        # Add the leaf nodes
        for aUniqueLeafBehavior in self.uniqueBehaviors:
            parentNodeName = self.leaf_to_behavior_groups_dict[aUniqueLeafBehavior]
            parentNode = newRootNode.find_child(parentNodeName)
            if parentNode:
                # found parent
                aNewNode = BehaviorNode(aUniqueLeafBehavior, self.color_dictionary[aUniqueLeafBehavior], parentNode)
                parentNode.add_child(aNewNode)
            else:
                print('Failed to find the parent node with name: ', parentNodeName)
            
        return newRootNode

    def get_unique_behaviors(self):
        return self.uniqueBehaviors

    def get_unique_behavior_groups(self):
        return self.uniqueBehaviorGroups

    def get_unique_behavior_activity_groups(self):
        return self.uniqueActivityGroups


    # "Types": grouped sets of behaviors
    def get_type(self, type_id):
        return self.uniqueBehaviors[type_id]

    def get_type_color(self, type_id):
        return self.get_type(type_id)
    
    # "Subtypes": the most specific set of behaviors
    def get_subtype(self, subtype_id):
        return self.uniqueBehaviors[subtype_id]

    def get_subtype_color(self, subtype_id):
        return self.color_dictionary[self.get_subtype(subtype_id)]

        self.groups_color_dictionary

    


    # def addMail(self, model, mailFrom, subject, date):
    #     model.insertRow(0)
    #     model.setData(model.index(0, self.BEHAVIOR_COL), mailFrom)
    #     model.setData(model.index(0, self.INFO_COL), subject)
    #     model.setData(model.index(0, self.COLOR_COL), date)

    def get_tree_model(self, parent):
        model = QStandardItemModel(0, 3, parent)
        model.setHeaderData(self.BEHAVIOR_COL, Qt.Horizontal, "Behavior")
        model.setHeaderData(self.INFO_COL, Qt.Horizontal, "Info")
        model.setHeaderData(self.COLOR_COL, Qt.Horizontal, "Color")
        return model

        
    @staticmethod
    def get_behaviors_list():
        return ['Awaken',
            'Chew',
            'Come Down',
            'Come Down From Partially Reared',
            'Come Down To Partially Reared',
            'ComeDown(CDtoPR, CDfromPR)',
            'Dig',
            'Drink Spout1',
            'Eat Zone1',
            'Eat Zone2',
            'Forage',
            'Groom',
            'Hang Cuddled',
            'Hang Vertically From Rear Up',
            'HangCuddled(HangCudl, RemainHC)',
            'HangVertically From HangCuddled',
            'HangVertically(HVfromHC, RemainHV)',
            'HangVertically(HVfromRU, HVfromHC, RemainHV)',
            'HangVertically(HVfromRU, RemainHV)',
            'HangVertically(HVfromRU, RemainHV, HVfromRU)',
            'HangVertically(HVfromRU, RemainHV, HVfromRU, RemainHV)',
            'HangVertically(HVfromRU, RemainHV, HVfromRU, RemainHV, HVfromRU, RemainHV)',
            'Jump',
            'Land Vertically',
            'Pause',
            'Rear Up',
            'Rear up Full From Partial',
            'Rear up Partially',
            'RearUp(RUfromPR, RemainRU)',
            'RearUp(RUfromPR, RemainRU, RUfromPR, RemainRU)',
            'RearUp(RUtoPR, RUfromPR)',
            'RearUp(RUtoPR, RUfromPR, RemainRU)',
            'RearUp(RearUp, RemainRU)',
            'Remain Hang Cuddled',
            'Remain Hang Vertically',
            'Remain Low',
            'Remain Partially Reared',
            'Remain RearUp',
            'Sleep',
            'Sniff',
            'Stationary',
            'Stretch Body',
            'Turn',
            'Twitch',
            'Unknown Behavior',
            'Walk Left',
            'Walk Right',
            'Walk Slowly'
        ]

    @staticmethod
    def get_behaviors_group_names_list():
        return [
            'Awaken',
            'Chew',
            'Come Down',
            'Come Down',
            'Come Down',
            'Come Down',
            'Dig',
            'Drink',
            'Eat',
            'Eat',
            'Forage',
            'Groom',
            'Hang',
            'Hang',
            'Hang',
            'Hang',
            'Hang',
            'Hang',
            'Hang',
            'Hang',
            'Hang',
            'Hang',
            'Jump',
            'Land Vertically',
            'Pause',
            'Rear Up',
            'Rear Up',
            'Rear Up',
            'Rear Up',
            'Rear Up',
            'Rear Up',
            'Rear Up',
            'Rear Up',
            'Hang',
            'Hang',
            'Remain Low',
            'Remain Partially Reared',
            'Rear Up',
            'Sleep',
            'Sniff',
            'Stationary',
            'Stretch Body',
            'Turn',
            'Twitch',
            'Unknown Behavior',
            'Walk',
            'Walk',
            'Walk'
        ]

    @staticmethod
    def get_behaviors_colors():
        colors_list = BehaviorsManager.get_behaviors_color_list()
        out_color_list = []
        for aColorListTriple in colors_list:
            transformedList = np.array(aColorListTriple)*255
            out_color = QColor(int(transformedList[0]), int(transformedList[1]), int(transformedList[2]))
            out_color_list.append(out_color)
        return out_color_list

    @staticmethod
    def get_behaviors_color_list():
        return [
            [0,0,0.666666666666667],
            [0,0,0.833333333333333],
            [0,0,1],
            [0,0,1],
            [0,0,1],
            [0,0,1],
            [0,0.166666666666667,1],
            [0,0.333333333333333,1],
            [0,0.500000000000000,1],
            [0,0.500000000000000,1],
            [0,0.666666666666667,1],
            [0,0.833333333333333,1],
            [0,1,1],
            [0,1,1],
            [0,1,1],
            [0,1,1],
            [0,1,1],
            [0,1,1],
            [0,1,1],
            [0,1,1],
            [0,1,1],
            [0,1,1],
            [0.166666666666667,1,0.833333333333333],
            [0.333333333333333,1,0.666666666666667],
            [0.500000000000000,1,0.500000000000000],
            [0.666666666666667,1,0.333333333333333],
            [0.666666666666667,1,0.333333333333333],
            [0.666666666666667,1,0.333333333333333],
            [0.666666666666667,1,0.333333333333333],
            [0.666666666666667,1,0.333333333333333],
            [0.666666666666667,1,0.333333333333333],
            [0.666666666666667,1,0.333333333333333],
            [0.666666666666667,1,0.333333333333333],
            [0,1,1],
            [0,1,1],
            [0.833333333333333,1,0.166666666666667],
            [1,1,0],
            [0.666666666666667,1,0.333333333333333],
            [1,0.833333333333333,0],
            [1,0.666666666666667,0],
            [1,0.500000000000000,0],
            [1,0.333333333333333,0],
            [1,0.166666666666667,0],
            [1,0,0],
            [0.833333333333333,0,0],
            [0.666666666666667,0,0],
            [0.666666666666667,0,0],
            [0.500000000000000,0,0],
        ]

    @staticmethod
    def get_behaviors_activity_groups_list():
        return ['Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Drink',
            'Eat',
            'Eat',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Resting Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Sleep',
            'Active Wakefulness',
            'Resting Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness',
            'Unknown Behavior',
            'Active Wakefulness',
            'Active Wakefulness',
            'Active Wakefulness'
        ]


