# coding: utf-8
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

from GUI.Model.Events.PhoDurationEvent_Video import PhoDurationEvent_Video

# (Animal, BehavioralBox, Context, Experiment, Labjack, FileParentFolder, StaticFileExtension, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent, VideoFile)

"""
The "@classmethod
    def getTableMapping(cls):"
    definintions are used by alchemical_model.py (called from the database connection object) to return a read/write table model from the database table.
    not required for default operation with SQLAlchemy
    The format is:
        # list of column 4-tuples(header, sqlalchemy column, column name, extra parameters as dict
        # if the sqlalchemy column object is Entity.name, then column name should probably be name,
        # Entity.name is what will be used when setting data, and sorting, 'name' will be used to retrieve the data.

Mapping Helpers (unused, currently creating table mappings manually):

    insp.all_orm_descriptors.keys()
    ['fullname', 'nickname', 'name', 'id']

"""
## This "Mixin" adds these columns and relationships to any file that inherits from it
# See https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/mixins.html for more info
class ReferenceBoxExperCohortAnimalMixin(object):
    # @declared_attr
    # def address_id(cls):
    #     return Column(Integer, ForeignKey('address.id'))

    @declared_attr
    def behavioral_box_id(cls):
        return Column(Integer, ForeignKey('BehavioralBoxes.id'), nullable=True)

    @declared_attr
    def experiment_id(cls):
        return Column(Integer, ForeignKey('Experiments.id'), nullable=True)

    @declared_attr
    def cohort_id(cls):
        return Column(Integer, ForeignKey('Cohorts.id'), nullable=True)

    @declared_attr
    def animal_id(cls):
        return Column(Integer, ForeignKey('Animals.id'), nullable=True)

    ## Relationships:
    @declared_attr
    def animal(cls):
        return relationship("Animal")

    @declared_attr
    def behavioral_box(cls):
        return relationship("BehavioralBox")

    @declared_attr
    def cohort(cls):
        return relationship("Cohort")

    @declared_attr
    def experiment(cls):
        return relationship("Experiment")

    # @classmethod
    # def getTableMapping(cls):
    #     return [
    #         ('BB ID', cls.behavioral_box_id, 'behavioral_box_id', {'editable': True}),
    #         ('ExperimentID', cls.experiment_id, 'experiment_id', {'editable': True}),
    #         ('CohortID', cls.cohort_id, 'cohort_id', {'editable': True}),
    #         ('AnimalID', cls.animal_id, 'animal_id', {'editable': True}),
    #     ]
    






class Animal(Base):
    __tablename__ = 'Animals'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True, server_default=text("'animal_0'"))
    birth_date = Column(Integer)
    receive_date = Column(Integer)
    death_date = Column(Integer)
    notes = Column(Text)

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('Name', cls.name, 'name', {'editable': True}),
            ('Birth Date', cls.birth_date, 'birth_date', {'editable': True}),
            ('Receive Date', cls.receive_date, 'receive_date', {'editable': True}),
            ('Death Date', cls.death_date, 'death_date', {'editable': True}),
            ('Notes', cls.notes, 'notes', {'editable': True}),
        ]
    


class BehavioralBox(Base):
    __tablename__ = 'BehavioralBoxes'

    id = Column(Integer, primary_key=True)
    # numerical_id = Column(Integer, nullable=False)
    name = Column(Text, server_default=text("'B00'"), unique=True, nullable=False)

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            # ('NumericalID', cls.numerical_id, 'numerical_id', {'editable': True}),
            ('Name', cls.name, 'name', {'editable': True}),
        ]



class Subcontext(Base):
    __tablename__ = 'Subcontext'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    parent_context = Column(Integer, ForeignKey('Contexts.id'), nullable=False, server_default=text("1"))
    notes = Column(Text)

    parentContext = relationship('Context', back_populates="subcontexts")

    def __init__(self,id,name,parent_context,notes=None):
        self.id = id
        self.name = name
        self.parent_context = parent_context
        self.notes = notes

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('Name', cls.name, 'name', {'editable': True}),
            ('Parent ID', cls.parent_context, 'parent_context', {'editable': True}),
            ('Notes', cls.notes, 'notes', {'editable': True}),
        ]

    __table_args__ = (UniqueConstraint('name', 'parent_context', name='_name_parent_uc'),
                     )

class Context(Base):
    __tablename__ = 'Contexts'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    note = Column(Text)

    subcontexts = relationship('Subcontext', order_by=Subcontext.id, back_populates="parentContext")

    def __init__(self,id,name,notes=None):
        self.id = id
        self.name = name
        self.notes = notes

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('Name', cls.name, 'name', {'editable': True}),
            ('Notes', cls.note, 'note', {'editable': True}),
        ]


class Experiment(Base):
    __tablename__ = 'Experiments'

    id = Column(Integer, primary_key=True)
    name = Column(Text, server_default=text("'experiment_'"))
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer)
    notes = Column(Text)

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('Name', cls.name, 'name', {'editable': True}),
            ('StartDate', cls.start_date, 'start_date', {'editable': True}),
            ('EndDate', cls.end_date, 'end_date', {'editable': True}),
            ('Notes', cls.notes, 'notes', {'editable': True}),
        ]


class Labjack(Base):
    __tablename__ = 'Labjacks'

    serial_number = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, server_default=text("'LJ-'"))
    model = Column(Text, server_default=text("'T7'"))

    @classmethod
    def getTableMapping(cls):
        return [
            ('SerialNumber', cls.serial_number, 'serial_number', {'editable': True}),
            ('Name', cls.name, 'name', {'editable': True}),
            ('Model', cls.model, 'model', {'editable': True}),
        ]


# t_sqlite_sequence = Table(
#     'sqlite_sequence', metadata,
#     Column('name', NullType),
#     Column('seq', NullType)
# )


class StaticFileExtension(Base):
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


class Cohort(Base):
    __tablename__ = 'Cohorts'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True, server_default=text("'cohort_'"))
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer)
    experiment = Column(Integer, ForeignKey('Experiments.id', ondelete='SET NULL'))

    Experiment = relationship('Experiment')

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('Name', cls.name, 'name', {'editable': True}),
            ('StartDate', cls.start_date, 'start_date', {'editable': True}),
            ('EndDate', cls.end_date, 'end_date', {'editable': True}),
            ('ExperimentID', cls.experiment, 'experiment', {'editable': True}), # TODO: should we disable this column?
        ]




"""
"Partitions"
Datatypes:
Interval: datetime.timedelta()
Numeric
"""
class CategoricalDurationLabel(ReferenceBoxExperCohortAnimalMixin, Base):
    __tablename__ = 'CategoricalDurationLabels'

    id = Column(Integer, primary_key=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    label_created_date = Column(DateTime, nullable=False)
    label_created_user = Column(Text, nullable=False, server_default=text("Anonymous"))
    last_updated_date = Column(DateTime, nullable=False)
    last_updated_user = Column(Text, nullable=False, server_default=text("Anonymous"))

    context_id = Column(Integer, ForeignKey('Contexts.id'))
    subcontext_id = Column(Integer, ForeignKey('Subcontext.id'))

    # type, subtype are the main properties. Either property can be Null/None when the user hasn't yet labeled the partition
    type_id = Column(Integer)
    subtype_id = Column(Integer)
    tertiarytype_id = Column(Integer)

    primary_text = Column(Text)
    secondary_text = Column(Text)
    tertiary_text = Column(Text)

    notes = Column(Text)

    Context = relationship('Context', foreign_keys=[context_id])
    Subcontext = relationship('Subcontext', foreign_keys=[subcontext_id])

    # def __init__(self,id,start_date,end_date,label_created_date,label_created_user,last_updated_date,last_updated_user,context_id,subcontext_id,\
    #      type_id, subtype_id, tertiarytype_id, primary_text, secondary_text, tertiary_text, notes):
    #     self.id = id
    #     self.start_date = start_date
    #     self.end_date = end_date
    #     self.label_created_date = label_created_date
    #     self.label_created_user = label_created_user
    #     self.last_updated_date = last_updated_date
    #     self.last_updated_user = last_updated_user

    #     self.context_id = context_id
    #     self.subcontext_id = subcontext_id

    #     self.type_id = type_id
    #     self.subtype_id = subtype_id
    #     self.tertiarytype_id = tertiarytype_id

    #     self.primary_text = primary_text
    #     self.secondary_text = secondary_text
    #     self.tertiary_text = tertiary_text

    #     self.notes = notes

    # __table_args__ = (UniqueConstraint('start_date', 'end_date', 'type_id', 'subtype_id', 'tertiarytype_id' name='_customer_location_uc'),
    #                  )

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('StartDate', cls.start_date, 'start_date', {'editable': False}),
            ('EndDate', cls.end_date, 'end_date', {'editable': False}),
            ('CreatedDate', cls.label_created_date, 'label_created_date', {'editable': False}),
            ('CreatedUser', cls.label_created_user, 'label_created_user', {'editable': False}),
            ('LastUpdatedDate', cls.last_updated_date, 'last_updated_date', {'editable': False}),
            ('LastUpdatingUser', cls.last_updated_user, 'last_updated_user', {'editable': False}),
            ('Context ID', cls.context, 'context', {'editable': True}),
            ('Subcontext ID', cls.subcontext, 'subcontext', {'editable': True}),
            ('Type ID', cls.type, 'type', {'editable': True}),
            ('Subtype ID', cls.subtype, 'subtype', {'editable': True}),
            ('TertiaryType ID', cls.tertiarytype_id, 'tertiarytype_id', {'editable': True}),
            ('PrimaryTxt', cls.primary_text, 'primary_text', {'editable': True}),
            ('SecondaryTxt', cls.secondary_text, 'secondary_text', {'editable': True}),
            ('TertiaryTxt', cls.tertiary_text, 'tertiary_text', {'editable': True}),
            ('Notes', cls.notes, 'notes', {'editable': True}),
            ('BB ID', cls.behavioral_box_id, 'behavioral_box_id', {'editable': True}),
            ('ExperimentID', cls.experiment_id, 'experiment_id', {'editable': True}),
            ('CohortID', cls.cohort_id, 'cohort_id', {'editable': True}),
            ('AnimalID', cls.animal_id, 'animal_id', {'editable': True}),
        ]

    # __table_args__ = (UniqueConstraint('context_id', 'subcontext_id', name='_name_parent_uc'),
    #                  )
        __table_args__ = (UniqueConstraint('context_id','subcontext_id','behavioral_box_id','experiment_id','cohort_id','animal_id', name="uix_context_filters_uc"))



class TimestampedAnnotation(ReferenceBoxExperCohortAnimalMixin, Base):
    __tablename__ = 'TimestampedAnnotations'

    id = Column(Integer, primary_key=True)
    start_date = Column(Integer)
    end_date = Column(Integer)


    context = Column(Integer, ForeignKey('Contexts.id'), server_default=text("1"))
    subcontext = Column(Integer, ForeignKey('Subcontext.id'))

    type = Column(Integer, nullable=False, server_default=text("1"))
    subtype = Column(Integer, nullable=False, server_default=text("1"))
    primary_text = Column(Text, nullable=False)
    secondary_text = Column(Text)
    tertiary_text = Column(Text)
    overflow_text = Column(Text)


    Context = relationship('Context', foreign_keys=[context])
    Subcontext = relationship('Subcontext', foreign_keys=[subcontext])

    """
    TimestampedAnnotation:
        .context = Column(Integer, ForeignKey('Contexts.id'), server_default=text("1"))
        Context = relationship('Context')
    """

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('StartDate', cls.start_date, 'start_date', {'editable': False}),
            ('EndDate', cls.end_date, 'end_date', {'editable': False}),
            ('Context ID', cls.context, 'context', {'editable': True}),
            ('Subcontext ID', cls.subcontext, 'subcontext', {'editable': True}),
            ('Type ID', cls.type, 'type', {'editable': True}),
            ('Subtype ID', cls.subtype, 'subtype', {'editable': True}),
            ('PrimaryTxt', cls.primary_text, 'primary_text', {'editable': True}),
            ('SecondaryTxt', cls.secondary_text, 'secondary_text', {'editable': True}),
            ('TertiaryTxt', cls.tertiary_text, 'tertiary_text', {'editable': True}),
            ('OverflowTxt', cls.overflow_text, 'overflow_text', {'editable': True}),
            ('BB ID', cls.behavioral_box_id, 'behavioral_box_id', {'editable': True}),
            ('ExperimentID', cls.experiment_id, 'experiment_id', {'editable': True}),
            ('CohortID', cls.cohort_id, 'cohort_id', {'editable': True}),
            ('AnimalID', cls.animal_id, 'animal_id', {'editable': True}),
        ]



class ExperimentalConfigurationEvent(Base):
    __tablename__ = 'ExperimentalConfigurationEvents'

    id = Column(Integer, primary_key=True)
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer)
    experiment_id = Column(Integer, ForeignKey('Experiments.id'))
    cohort_id = Column(Integer, ForeignKey('Cohorts.id'))
    animal_id = Column(Integer, ForeignKey('Animals.id'))
    labjack_id = Column(Integer, ForeignKey('Labjacks.serial_number'))
    behavioralbox_id = Column(Integer, ForeignKey('BehavioralBoxes.id'))
    notes = Column(Text)
    event_type = Column(Text)
    event_subtype = Column(Text)

    animal = relationship('Animal')
    behavioralbox = relationship('BehavioralBox')
    cohort = relationship('Cohort')
    experiment = relationship('Experiment')
    labjack = relationship('Labjack')


class VideoFile(ReferenceBoxExperCohortAnimalMixin, Base):
    __tablename__ = 'VideoFile'

    id = Column(Integer, primary_key=True)
    file_fullname = Column(Text, nullable=False)
    file_basename = Column(Text, nullable=False)
    file_extension = Column(Text, ForeignKey('staticFileExtensions.extension'), nullable=False)
    # file_extension = Column(Integer, ForeignKey('staticFileExtensions.extension'), nullable=False)
    file_video_folder = Column(Integer, ForeignKey('fileParentFolders.id'))
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer)
    duration = Column(Integer)
    # behavioral_box_id = Column(Integer, ForeignKey('BehavioralBoxes.id'))
    # experiment_id = Column(Integer, ForeignKey('Experiments.id'))
    # cohort_id = Column(Integer, ForeignKey('Cohorts.id'))
    # animal_id = Column(Integer, ForeignKey('Animals.id'))
    is_original_video = Column(Integer)
    notes = Column(Text)

    # animal = relationship('Animal')
    # behavioral_box = relationship('BehavioralBox')
    # cohort = relationship('Cohort')
    # experiment = relationship('Experiment')
    staticFileExtension = relationship('StaticFileExtension')
    fileParentFolder = relationship('FileParentFolder', back_populates="videoFiles")

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('FullName', cls.file_fullname, 'file_fullname', {'editable': True}),
            # ('BaseName', cls.file_basename, 'file_basename', {'editable': True}),
            # ('FileExtension ID', cls.file_extension, 'file_extension', {'editable': True}),
            ('Parent Folder ID', cls.file_video_folder, 'file_video_folder', {'editable': True}),
            ('StartDate', cls.start_date, 'start_date', {'editable': False}),
            ('EndDate', cls.end_date, 'end_date', {'editable': False}),
            ('Duration', cls.duration, 'duration', {'editable': False}),
            ('BB ID', cls.behavioral_box_id, 'behavioral_box_id', {'editable': True}),
            ('ExperimentID', cls.experiment_id, 'experiment_id', {'editable': True}),
            ('CohortID', cls.cohort_id, 'cohort_id', {'editable': True}),
            ('AnimalID', cls.animal_id, 'animal_id', {'editable': True}),
            ('Is Original?', cls.is_original_video, 'is_original_video', {'editable': False}),
            ('Notes', cls.notes, 'notes', {'editable': True}),
        ]


    def __init__(self,id,file_fullname,file_basename,file_extension,file_video_folder,start_date,end_date,duration,behavioral_box_id,experiment_id,cohort_id,animal_id,is_original_video,notes=None):
        self.id = id
        self.file_fullname = file_fullname
        self.file_basename = file_basename
        self.file_extension = file_extension
        self.file_video_folder = file_video_folder
        self.start_date = start_date
        self.end_date = end_date
        self.duration = duration
        self.behavioral_box_id = behavioral_box_id
        self.experiment_id = experiment_id
        self.cohort_id = cohort_id
        self.animal_id = animal_id
        self.is_original_video = is_original_video
        self.notes = notes

    def get_start_date(self):
        return datetime.fromtimestamp(float(self.start_date) / 1000.0)

    def get_end_date(self):
        return datetime.fromtimestamp(float(self.end_date) / 1000.0)

    def get_duration(self):
        return float(self.duration) / 1000.0

    def get_extension(self):
        return ('.' + self.file_extension)  # Add the period back on

    def get_full_path(self):
        entries = Path(self.get_parent_path())
        return entries.joinpath(self.file_fullname).resolve(strict=False)

    def get_parent_path(self):
        parentFolder = self.fileParentFolder
        aFullParentPath = parentFolder.fullpath
        return aFullParentPath

    def get_is_original_video(self):
        # Allow being undecided as to whether a video is an original or not
        if (self.is_original_video is None):
            return None
        else:
            return self.is_original_video

    def get_is_deeplabcut_labeled_video(self):
        # Allow being undecided as to whether a video is an original or not
        if (self.is_original_video is None):
            return None
        else:
            return (not self.is_original_video)

    def get_behavioral_box_id(self):
        if (self.behavioral_box_id is None):
            return None
        else:
            return (self.behavioral_box_id - 1)

    def get_currProperties(self):
        return {'duration': self.get_duration()}

    def get_extendedProperties(self):
        return {'behavioral_box_id': self.behavioral_box_id}

    def get_output_dict(self):
        return {'base_name': self.file_basename, 'file_fullname': self.file_fullname, 'file_extension': self.get_extension(), 'parent_path': self.file_video_folder, 'path': self.get_full_path(), 'parsed_date': self.get_start_date(), 'computed_end_date': self.get_end_date(), 'is_deeplabcut_labeled_video': self.get_is_deeplabcut_labeled_video(), 'properties': self.get_currProperties(), 'extended_properties': self.get_extendedProperties()}

    # returns a "VideoInfo" object
    def get_video_info_obj(self):
        parentFolder = self.fileParentFolder
        aFullParentPath = parentFolder.fullpath
        newExperimentContextInfoObj = ExperimentContextInfo(self.id, self.get_behavioral_box_id(), self.experiment_id, self.cohort_id, self.animal_id, self.notes)
        newVideoInfoObj = VideoInfo(self.file_fullname, self.file_basename, self.get_extension(), aFullParentPath, \
             self.get_start_date().replace(tzinfo=None), self.get_end_date().replace(tzinfo=None), self.get_duration(), self.get_is_original_video(), newExperimentContextInfoObj)
        return newVideoInfoObj

    # returns a "VideoParsedResults" object
    def get_parsed_video_result_obj(self):
        parsedResults = VideoParsedResults(self.get_duration())
        newResultsObj = FoundVideoFileResult(str(self.get_full_path()), self.get_parent_path(), self.file_basename, self.file_fullname, self.get_extension(), \
            self.get_start_date().replace(tzinfo=None), self.get_behavioral_box_id(), self.get_is_deeplabcut_labeled_video())
        newResultsObj.video_parsed_results = parsedResults
        return newResultsObj


    @staticmethod
    def from_parsed_video_result_obj(aParsedVideoResultObj, anExperimentID = 1, aCohortID = 1, anAnimalID = 3, notes= ''):
        aFullPath = str(aParsedVideoResultObj.path)
        aFullParentPath = str(aParsedVideoResultObj.parent_path)  # The parent path
        aFullName = aParsedVideoResultObj.full_name  # The full name including extension
        aBaseName = aParsedVideoResultObj.base_name  # Excluding the period and extension
        anExtension = aParsedVideoResultObj.file_extension[1:]  # the file extension excluding the period
        if (not aParsedVideoResultObj.behavioral_box_id is None):
            aBBID = aParsedVideoResultObj.behavioral_box_id + 1  # Add one to get a valid index
        else:
            aBBID = 1

        if (not aParsedVideoResultObj.is_deeplabcut_labeled_video is None):
            is_deeplabcut_labeled_video = aParsedVideoResultObj.is_deeplabcut_labeled_video
            is_original_video = (not is_deeplabcut_labeled_video)
        else:
            is_deeplabcut_labeled_video = None
            is_original_video = None  # We know nothing about whether it is an original video

        startTime = int(aParsedVideoResultObj.parsed_date.timestamp() * 1000.0)
        endTime = int(aParsedVideoResultObj.get_computed_end_date().timestamp() * 1000.0)
        duration = int(aParsedVideoResultObj.get_duration().total_seconds() * 1000.0)

        return VideoFile(None, aFullName, aBaseName, anExtension, aFullParentPath, startTime, endTime, duration, aBBID, anExperimentID, aCohortID, anAnimalID, is_original_video, notes)

    @staticmethod
    def get_gui_view(aVideoRecord, parent=None):
        currExtraInfoDict = aVideoRecord.get_output_dict()
        outGuiObj = PhoDurationEvent_Video(aVideoRecord.get_start_date(), aVideoRecord.get_end_date(), aVideoRecord.file_fullname, QColor(51,204,255), currExtraInfoDict, parent=parent)
        # outGuiObj
        return outGuiObj


class FileParentFolder(Base):
    __tablename__ = 'fileParentFolders'

    id = Column(Integer, primary_key=True)
    fullpath = Column(Text, nullable=False, server_default=text("'\\WATSON-BB-OVERS\ServerInternal-01\Transcoded Videos\BB00\'"))
    root = Column(Text, nullable=False, server_default=text("'\\WATSON-BB-OVERS\'"))
    path = Column(Text, nullable=False, server_default=text("'ServerInternal-01\Transcoded Videos\BB00\'"))
    notes = Column(Text)

    videoFiles = relationship("VideoFile", order_by=VideoFile.start_date, back_populates="fileParentFolder")

    def __init__(self,id,fullpath,root,path,notes=None):
        self.id = id
        self.fullpath = str(fullpath)
        self.root = str(root)
        self.path = str(path)
        self.notes = notes

    @staticmethod
    def from_path_string(path_string):
        path = Path(path_string)
        path.anchor

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('Full Path', cls.fullpath, 'fullpath', {'editable': True}),
            ('Root', cls.root, 'root', {'editable': True}),
            ('Leaf Path', cls.path, 'path', {'editable': True}),
            ('Notes', cls.notes, 'notes', {'editable': True}),
        ]
