# EdgeAndCornerSelectionViewHelpers.py

import sys
from enum import Enum, IntFlag, IntEnum

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize, QMargins, Q_FLAGS
from PyQt5.QtGui import QColor, QCursor, QPainterPath, QBrush
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QMenu, QLabel, QMainWindow

## IMPORT:
# from GUI.UI.EdgeAndCornerSelectionViewHelpers import EdgeAndCornerContainerComponent, EdgeAndCornerContainerViewMixin

class EdgeAndCornerContainerComponent(IntEnum):
    NONE = 0,
    BODY = 1,
    Corner_TL = 2,
    Edge_Top = 4,
    Corner_TR = 8,
    Edge_Right = 16,
    Corner_BR = 32,
    Edge_Bottom = 64,
    Corner_BL = 128,
    Edge_Left = 256

    # Note Margins are QMargins(int left, int top, int right, int bottom)

    def get_highlight_rect(self, parent_rect, border_handle_size_diff):
        const_corner_rect_size = QSize(10, 10)
        currRect = QRect(QPoint(0, 0), const_corner_rect_size)
        
        if (self == EdgeAndCornerContainerComponent.Corner_TL):
            currPoint = parent_rect.topLeft()
            currRect.moveTopLeft(currPoint)
        elif (self == EdgeAndCornerContainerComponent.Corner_TR):
            currPoint = parent_rect.topRight()
            currRect.moveTopRight(currPoint)
        elif (self == EdgeAndCornerContainerComponent.Corner_BR):
            currPoint = parent_rect.bottomRight()
            currRect.moveBottomRight(currPoint)
        elif (self == EdgeAndCornerContainerComponent.Corner_BL):
            currPoint = parent_rect.bottomLeft()
            currRect.moveBottomLeft(currPoint)
        elif (self == EdgeAndCornerContainerComponent.Edge_Top):
            # currPoint = parent_rect.top()
            # currRect = QRect(currPoint, const_corner_rect_size))
            currMargins = QMargins(0,border_handle_size_diff,0,0)
            contents_rect = parent_rect.marginsRemoved(currMargins)
            currRect.setLeft(parent_rect.left())
            currRect.setRight(parent_rect.right())
            currRect.setTop(parent_rect.top())
            currRect.setBottom(contents_rect.top())
            # currRect.setHeight(border_handle_size_diff)
        elif (self == EdgeAndCornerContainerComponent.Edge_Right):
            # currPoint = parent_rect.top()
            # currRect = QRect(currPoint, const_corner_rect_size))
            currMargins = QMargins(0,0,border_handle_size_diff,0)
            contents_rect = parent_rect.marginsRemoved(currMargins)
            currRect.setLeft(contents_rect.right())
            currRect.setRight(parent_rect.right())
            currRect.setTop(parent_rect.top())
            currRect.setBottom(parent_rect.bottom())
            # currRect.setHeight(border_handle_size_diff)
        elif (self == EdgeAndCornerContainerComponent.Edge_Bottom):
            # currPoint = parent_rect.top()
            # currRect = QRect(currPoint, const_corner_rect_size))
            currMargins = QMargins(0,0,0,border_handle_size_diff)
            contents_rect = parent_rect.marginsRemoved(currMargins)
            currRect.setLeft(parent_rect.left())
            currRect.setRight(parent_rect.right())
            # currRect.setTop(parent_rect.bottom()+border_handle_size_diff)
            currRect.setTop(contents_rect.bottom())
            currRect.setBottom(parent_rect.bottom())
            # currRect.setHeight(border_handle_size_diff)
        elif (self == EdgeAndCornerContainerComponent.Edge_Left):
            # currPoint = parent_rect.top()
            # currRect = QRect(currPoint, const_corner_rect_size))
            currMargins = QMargins(border_handle_size_diff,0,0,0)
            contents_rect = parent_rect.marginsRemoved(currMargins)
            currRect.setLeft(parent_rect.left())
            currRect.setRight(contents_rect.left())
            currRect.setTop(parent_rect.top())
            currRect.setBottom(parent_rect.bottom())
            # currRect.setHeight(border_handle_size_diff)
        else:
            currRect = None

        return currRect

    def get_mode_cursor(self):
        if (self == EdgeAndCornerContainerComponent.Corner_TL):
            return QCursor(QtCore.Qt.SizeFDiagCursor)
        elif (self == EdgeAndCornerContainerComponent.Corner_TR):
            return QCursor(QtCore.Qt.SizeBDiagCursor)
        elif (self == EdgeAndCornerContainerComponent.Corner_BR):
            return QCursor(QtCore.Qt.SizeFDiagCursor)
        elif (self == EdgeAndCornerContainerComponent.Corner_BL):
            return QCursor(QtCore.Qt.SizeBDiagCursor)
        elif (self == EdgeAndCornerContainerComponent.Edge_Top):
            return QCursor(QtCore.Qt.SizeVerCursor)
        elif (self == EdgeAndCornerContainerComponent.Edge_Right):
            return QCursor(QtCore.Qt.SizeHorCursor)
        elif (self == EdgeAndCornerContainerComponent.Edge_Bottom):
            return QCursor(QtCore.Qt.SizeVerCursor)
        elif (self == EdgeAndCornerContainerComponent.Edge_Left):
            return QCursor(QtCore.Qt.SizeHorCursor)
        elif (self == EdgeAndCornerContainerComponent.BODY):
            return QCursor(QtCore.Qt.SizeAllCursor)
        else:
            return QCursor(QtCore.Qt.ArrowCursor)


class EdgeAndCornerContainerViewMixin(object):

    def init_EdgeAndCornerContainerViewMixin(self):
        self.border_handle_size_diff = 3
        self.hoverEdgeRectColor = QColor(255,60,60,200)
        self.hoverEdgeRectFillBrush = QBrush(QColor(255,0,100,180), Qt.SolidPattern)
        self.hoveredEdgeAndCorners = EdgeAndCornerContainerComponent.NONE
        self.selectedEdgeAndCorners = EdgeAndCornerContainerComponent.NONE
        self.setMouseTracking(True)

    def try_add_component(self, new_component, is_updating_hover):
        if (is_updating_hover):
            oldValue = self.hoveredEdgeAndCorners
            self.hoveredEdgeAndCorners = self.hoveredEdgeAndCorners.value | new_component
            return (oldValue.value != self.hoveredEdgeAndCorners.value)
        else:
            # otherwise updating selection
            oldValue = self.selectedEdgeAndCorners
            self.selectedEdgeAndCorners = self.selectedEdgeAndCorners.value | new_component
            return (oldValue.value != self.selectedEdgeAndCorners.value)


    # It seems most of the magic is being done here. This function sets the cursor shape (whether it's a "resizing" handle or a mouse) and sets the "mode" variable to indicate which mode it's currently in.,
    def updateEdgeAndCornerContainerActivePosition(self, e_pos: QPoint, is_updating_hover):
        didModeChange = False
        # Clear the previous selections
        if is_updating_hover:
            self.hoveredEdgeAndCorners = EdgeAndCornerContainerComponent.NONE
        else:
            self.selectedEdgeAndCorners = EdgeAndCornerContainerComponent.NONE

        # Check corners
        # Left - Bottom
        if (((e_pos.y() > self.y() + self.height() - self.border_handle_size_diff) and # Bottom
            (e_pos.x() < self.x() + self.border_handle_size_diff)) or # Left
        # Right-Bottom
        ((e_pos.y() > self.y() + self.height() - self.border_handle_size_diff) and # Bottom
        (e_pos.x() > self.x() + self.width() - self.border_handle_size_diff)) or # Right
        # Left-Top
        ((e_pos.y() < self.y() + self.border_handle_size_diff) and # Top
        (e_pos.x() < self.x() + self.border_handle_size_diff)) or # Left
        # Right-Top
        (e_pos.y() < self.y() + self.border_handle_size_diff) and # Top
        (e_pos.x() > self.x() + self.width() - self.border_handle_size_diff)): # Right
            # Left - Bottom
            if ((e_pos.y() > self.y() + self.height() - self.border_handle_size_diff) and # Bottom
            (e_pos.x() < self.x()
                + self.border_handle_size_diff)): # Left
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.Corner_BL, is_updating_hover)
                # Right - Bottom
            if ((e_pos.y() > self.y() + self.height() - self.border_handle_size_diff) and # Bottom
            (e_pos.x() > self.x() + self.width() - self.border_handle_size_diff)): # Right
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.Corner_BR, is_updating_hover)
            # Left - Top
            if ((e_pos.y() < self.y() + self.border_handle_size_diff) and # Top
            (e_pos.x() < self.x() + self.border_handle_size_diff)): # Left
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.Corner_TL, is_updating_hover)
            # Right - Top
            if ((e_pos.y() < self.y() + self.border_handle_size_diff) and # Top
            (e_pos.x() > self.x() + self.width() - self.border_handle_size_diff)): # Right
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.Corner_TR, is_updating_hover)

        # if we're ignoring the corners, try the edges
        
        # check cursor horizontal position (check left and right edges)
        if ((not didModeChange) and (e_pos.x() < self.x() + self.border_handle_size_diff) or # Left
            (e_pos.x() > self.x() + self.width() - self.border_handle_size_diff)): # Right
            if e_pos.x() < self.x() + self.border_handle_size_diff: # Left
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.Edge_Left, is_updating_hover)
            else: # Right
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.Edge_Right, is_updating_hover)

        # check cursor vertical position (check top and bottom edges)
        if ((not didModeChange) and (e_pos.y() > self.y() + self.height() - self.border_handle_size_diff) or # Bottom
            (e_pos.y() < self.y() + self.border_handle_size_diff)): # Top
            if e_pos.y() < self.y() + self.border_handle_size_diff: # Top
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.Edge_Top, is_updating_hover)
            else: # Bottom
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.Edge_Bottom, is_updating_hover)
        
        # Otherwise we're not hovering any corners or edges. Check and see if we're moving
        if (not didModeChange):
            didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.BODY, is_updating_hover)
            if (not didModeChange):
                # if we don't allow MOVE mode, set to NONE mode
                didModeChange = self.try_add_component(EdgeAndCornerContainerComponent.NONE, is_updating_hover)

        # Finally update the cursor
        if didModeChange:
            self.setCursor(self.mode.get_mode_cursor())
            self.update()


    def paintEvent_EdgeAndCornerContainerViewMixin(self, painter, drawRect):
        # Draw highlighted edges:
        # rect = e.rect()
        # rect.adjust(0,0,-1,-1)

        currHighlightRect = self.hoveredEdgeAndCorners.get_highlight_rect(drawRect, self.border_handle_size_diff)
        if currHighlightRect is not None:
            painter.setPen(self.hoverEdgeRectColor)
            painter.setBrush(self.hoverEdgeRectFillBrush)
            painter.drawRect(currHighlightRect)