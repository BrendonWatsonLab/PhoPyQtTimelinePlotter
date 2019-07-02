# phoDrawingShapes.py
# Contains the different shapes to draw and what they represent (instantaneous events, intervals, etc)
# https://www.e-education.psu.edu/geog489/node/2301
import sys 
from datetime import datetime, timezone, timedelta
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt, QPoint, QRect

class PhoEvent:

    def __init__(self, startTime = datetime.now(), name = '', color = Qt.black): 
         self.name = name
         self.startTime = startTime
         self.color = color
 
    def __eq__(self, otherEvent): 
            return self.name == otherEvent.name and self.startTime == otherEvent.startTime 
 
    # Less Than (<) operator
    def __lt__(self, otherEvent): 
           return self.startTime < otherEvent.startTime 

    def __str__(self): 
        return 'Event {0}: startTime: {1}, color: {2}'.format(self.name, self.startTime, self.color)

    # def move(self, deltaX, deltaY): 
    #     self.x += deltaX
    #     self.y += deltaY

    # "pass": specifies that we're leaving this method "virtual" or intensionally empty to be overriden by a subclass.
    def paint(self, painter, totalDuration, totalParentCanvasRect):
         pass




class PhoDurationEvent(PhoEvent):
    RectCornerRounding = 2

    def __init__(self, startTime = datetime.now(), endTime = None, name = '', color = Qt.black):
        super(PhoDurationEvent, self).__init__(startTime, name, color)
        self.endTime = endTime
 
    def __eq__(self, otherEvent): 
            return self.name == otherEvent.name and self.startTime == otherEvent.startTime and self.endTime == otherEvent.endTime
 
    # Less Than (<) operator
    def is_entirely_less_than(self, otherEvent):
        # Returns true if this event is entirely less than the otherEvent (meaning it both starts AND completes before the start of the otherEvent)
           return self.startTime < otherEvent.startTime and self.endTime < otherEvent.startTime

    def is_entirely_greater_than(self, otherEvent):
        # Returns true if this event is entirely greater than the otherEvent (meaning it both starts AND completes after the end of the otherEvent)
           return self.startTime > otherEvent.endTime and self.endTime > otherEvent.endTime

    # def overlaps(self, otherEvent):
    #     # Returns true if this event overlaps the otherEvent
    #     if otherEvent.end
    #     return self.

    def __str__(self): 
        return 'Event {0}: [startTime: {1}, endTime: {2}], duration: {3}'.format(self.name, self.startTime, self.endTime, self.computeDuration())

    def computeDuration(self):
        if self.endTime:
            return (self.endTime - self.startTime)
        else:
            return 0.0

    # def move(self, deltaX, deltaY): 
    #     self.x += deltaX
    #     self.y += deltaY

    # "pass": specifies that we're leaving this method "virtual" or intensionally empty to be overriden by a subclass.
    def paint(self, painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect):
        percentDuration = (self.computeDuration()/totalDuration)
        offsetStartDuration = self.startTime - totalStartTime
        percentOffsetStart = offsetStartDuration/totalDuration
        x = percentOffsetStart * totalParentCanvasRect.width()
        width = percentDuration * totalParentCanvasRect.width()
        height = totalParentCanvasRect.height()
        y = 0.0
        eventRect = QRect(x, y, width, height)
        # painter.setPen( QtGui.QPen( Qt.darkBlue, 2, join=Qt.MiterJoin ) )
        painter.setPen( QtGui.QPen( Qt.darkBlue, 0.0, join=Qt.MiterJoin ) )
        painter.setBrush( QBrush( self.color, Qt.SolidPattern ) )
        # painter.drawRect(eventRect )
        painter.drawRect( x, y, width, height )
        # painter.drawRoundedRect( x, y, width, height, PhoDurationEvent.RectCornerRounding, PhoDurationEvent.RectCornerRounding)
        # painter.drawRoundedRect( eventRect, PhoDurationEvent.RectCornerRounding, PhoDurationEvent.RectCornerRounding )
        painter.drawText( eventRect, Qt.AlignCenter, self.name )


## GUI CLASS
class GeometryDrawingWidget( QtWidgets.QWidget ):

    def __init__( self, objects, totalStartTime, totalEndTime ):
        super( GeometryDrawingWidget, self ).__init__()
        self.objectsToDraw = objects
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)

    def paintEvent( self, event ):
        qp = QtGui.QPainter()
        qp.begin( self )
        for obj in self.objectsToDraw:
            obj.paint( qp, self.totalStartTime, self.totalEndTime, self.totalDuration, event.rect())
        qp.end()


class MyMainWindow( QtWidgets.QMainWindow ):

    def __init__( self, objects, totalStartTime, totalEndTime ):
        super( MyMainWindow, self ).__init__()
        self.resize( 300, 300 )
        self.setCentralWidget( GeometryDrawingWidget( objects, totalStartTime, totalEndTime ) )



if __name__ == '__main__':
    square1 = Square(5, 5, 8) 
    print(square1.computeArea()) 
    print(square1.computePerimeter()) 
    square1.move(2,2)
    print(square1)
