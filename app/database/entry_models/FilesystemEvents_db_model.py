# coding: utf-8
import sys
from enum import Enum

from sqlalchemy import Column, ForeignKey, Integer, Table, Text, text, DateTime, UniqueConstraint
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from app.database.entry_models.DatabaseBase import Base, metadata
from pathlib import Path
from datetime import datetime

from GUI.Model.Videos import VideoInfo, ExperimentContextInfo

from app.filesystem.VideoUtils import VideoParsedResults, FoundVideoFileResult

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont

from GUI.Model.Events.PhoDurationEvent import PhoDurationEvent, PhoEvent

from GUI.Model.TrackType import TrackType
from GUI.Helpers.DateTimeRenders import DateTimeRenderMixin

from app.database.entry_models.db_model import ReferenceBoxExperCohortAnimalMixin, StartEndDatetimeMixin

# FilesystemEvents_db_model.py

## INCLUDES:
# from app.database.entry_models.FilesystemEvents_db_model import LabjackVariable_EventTypes, LabjackVariable_DispenseTypes


class LabjackVariable_EventTypes(Enum):
    Unknown = 1
    BeamBreak = 2
    Dispense = 3

    def get_short_str(self):
        if self == LabjackVariable_EventTypes.Unknown:
            return '?'
        elif self == LabjackVariable_EventTypes.BeamBreak:
            return 'B'
        elif self == LabjackVariable_EventTypes.Dispense:
            return 'D'
        else:
            return '!'

    def get_medium_str(self):
        if self == LabjackVariable_EventTypes.Unknown:
            return '???'
        elif self == LabjackVariable_EventTypes.BeamBreak:
            return 'BBr'
        elif self == LabjackVariable_EventTypes.Dispense:
            return 'Disp'
        else:
            return 'ERR'

    def get_long_str(self):
        if self == LabjackVariable_EventTypes.Unknown:
            return 'Unknown'
        elif self == LabjackVariable_EventTypes.BeamBreak:
            return 'BeamBreak'
        elif self == LabjackVariable_EventTypes.Dispense:
            return 'Dispense'
        else:
            return 'ERROR'

class LabjackVariable_DispenseTypes(Enum):
    Unknown = 1
    Water = 2
    Food = 3

    def get_short_str(self):
        if self == LabjackVariable_DispenseTypes.Unknown:
            return '?'
        elif self == LabjackVariable_DispenseTypes.Water:
            return 'W'
        elif self == LabjackVariable_DispenseTypes.Food:
            return 'F'
        else:
            return '!'

    def get_medium_str(self):
        if self == LabjackVariable_DispenseTypes.Unknown:
            return '???'
        elif self == LabjackVariable_DispenseTypes.Water:
            return 'Wat'
        elif self == LabjackVariable_DispenseTypes.Food:
            return 'Food'
        else:
            return 'ERR'

    def get_long_str(self):
        if self == LabjackVariable_DispenseTypes.Unknown:
            return 'Unknown'
        elif self == LabjackVariable_DispenseTypes.Water:
            return 'Water'
        elif self == LabjackVariable_DispenseTypes.Food:
            return 'Food'
        else:
            return 'ERROR'


class StaticEventType(Base):
    __tablename__ = 'staticFileExtensions'

    extension = Column(Text, primary_key=True, server_default=text("'mp4'"))
    description = Column(Text)
    notes = Column(Text)
    version = Column(Integer, server_default=text("0"))

    def __init__(self,extension,description=None,notes=None,version='0'):
        self.extension = extension
        self.description = description
        self.notes = notes
        self.version = version

    @staticmethod
    def from_path_string(path_string):
        path = Path(path_string)
        return StaticFileExtension(path.suffix, None, None, None)

    @classmethod
    def getTableMapping(cls):
        return [
            ('Extension', cls.extension, 'extension', {'editable': True}),
            ('Description', cls.description, 'description', {'editable': True}),
            ('Notes', cls.notes, 'notes', {'editable': True}),
            ('Version', cls.version, 'version', {'editable': True}),
        ]




# Parent of Behavior
class BehaviorGroup(Base):
    __tablename__ = 'behavior_groups'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    primary_color = Column(Integer, ForeignKey('category_colors.id'), nullable=False, server_default=text("1"))
    secondary_color = Column(Integer, ForeignKey('category_colors.id'), nullable=False, server_default=text("2"))
    note = Column(Text)

    primaryColor = relationship('CategoryColors', foreign_keys=[primary_color])
    secondaryColor = relationship('CategoryColors', foreign_keys=[secondary_color])

    behaviors = relationship("Behavior", order_by=Behavior.id, back_populates="parentGroup")

    def __init__(self,id,name,description,primary_color,secondary_color,note):
        self.id = id
        self.name = name
        self.description = description
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.note = note

