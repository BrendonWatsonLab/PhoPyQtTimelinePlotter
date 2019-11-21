# coding: utf-8
from sqlalchemy import Column, ForeignKey, Integer, Table, Text, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.database.entry_models.DatabaseBase import Base, metadata
from pathlib import Path
from datetime import datetime

from GUI.Model.Videos import VideoInfo, ExperimentContextInfo

from app.filesystem.VideoUtils import VideoParsedResults, FoundVideoFileResult
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

class Animal(Base):
    __tablename__ = 'Animals'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, server_default=text("'animal_0'"))
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

    numerical_id = Column(Integer, primary_key=True)
    name = Column(Text, server_default=text("'B00'"))

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.numerical_id, 'numerical_id', {'editable': False}),
            ('Name', cls.name, 'name', {'editable': True}),
        ]


class Context(Base):
    __tablename__ = 'Contexts'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    note = Column(Text)

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
    name = Column(Text, server_default=text("'LJ-'"))
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
    name = Column(Text, nullable=False, server_default=text("'cohort_'"))
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



class Subcontext(Base):
    __tablename__ = 'Subcontext'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    parent_context = Column(Integer, ForeignKey('Contexts.id'), nullable=False, server_default=text("1"))
    notes = Column(Text)

    Context = relationship('Context')

    @classmethod
    def getTableMapping(cls):
        return [
            ('ID', cls.id, 'id', {'editable': False}),
            ('Name', cls.name, 'name', {'editable': True}),
            ('Parent ID', cls.parent_context, 'parent_context', {'editable': True}),
            ('Notes', cls.notes, 'notes', {'editable': True}),
        ]



class TimestampedAnnotation(Base):
    __tablename__ = 'TimestampedAnnotations'

    id = Column(Integer, primary_key=True)
    start_date = Column(Integer)
    end_date = Column(Integer)
    context = Column(Integer, ForeignKey('Contexts.id'), server_default=text("1"))
    subcontext = Column(Integer, server_default=text("1"))
    type = Column(Integer, nullable=False, server_default=text("1"))
    subtype = Column(Integer, nullable=False, server_default=text("1"))
    primary_text = Column(Text, nullable=False)
    secondary_text = Column(Text)
    tertiary_text = Column(Text)
    overflow_text = Column(Text)

    Context = relationship('Context')

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
    behavioralbox_id = Column(Integer, ForeignKey('BehavioralBoxes.numerical_id'))
    notes = Column(Text)
    event_type = Column(Text)
    event_subtype = Column(Text)

    animal = relationship('Animal')
    behavioralbox = relationship('BehavioralBox')
    cohort = relationship('Cohort')
    experiment = relationship('Experiment')
    labjack = relationship('Labjack')


class VideoFile(Base):
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
    behavioral_box_id = Column(Integer, ForeignKey('BehavioralBoxes.numerical_id'))
    experiment_id = Column(Integer, ForeignKey('Experiments.id'))
    cohort_id = Column(Integer, ForeignKey('Cohorts.id'))
    animal_id = Column(Integer, ForeignKey('Animals.id'))
    is_original_video = Column(Integer)
    notes = Column(Text)

    animal = relationship('Animal')
    behavioral_box = relationship('BehavioralBox')
    cohort = relationship('Cohort')
    experiment = relationship('Experiment')
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

    def get_video_info_obj(self):
        parentFolder = self.fileParentFolder
        aFullParentPath = parentFolder.fullpath
        newExperimentContextInfoObj = ExperimentContextInfo(self.id, self.get_behavioral_box_id(), self.experiment_id, self.cohort_id, self.animal_id, self.notes)
        newVideoInfoObj = VideoInfo(self.file_fullname, self.file_basename, self.get_extension(), aFullParentPath, \
             self.get_start_date().replace(tzinfo=None), self.get_end_date().replace(tzinfo=None), self.get_duration(), self.get_is_original_video(), newExperimentContextInfoObj)
        return newVideoInfoObj

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
