# coding: utf-8
from sqlalchemy import Column, ForeignKey, Integer, Table, Text, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


# (Animal, BehavioralBox, Context, Experiment, Labjack, FileParentFolder, StaticFileExtension, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent, VideoFile)

class Animal(Base):
    __tablename__ = 'Animals'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, server_default=text("'animal_0'"))
    birth_date = Column(Integer)
    receive_date = Column(Integer)
    death_date = Column(Integer)
    notes = Column(Text)


class BehavioralBox(Base):
    __tablename__ = 'BehavioralBoxes'

    numerical_id = Column(Integer, primary_key=True)
    name = Column(Text, server_default=text("'B00'"))


class Context(Base):
    __tablename__ = 'Contexts'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    note = Column(Text)


class Experiment(Base):
    __tablename__ = 'Experiments'

    id = Column(Integer, primary_key=True)
    name = Column(Text, server_default=text("'experiment_'"))
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer)
    notes = Column(Text)


class Labjack(Base):
    __tablename__ = 'Labjacks'

    serial_number = Column(Integer, primary_key=True)
    name = Column(Text, server_default=text("'LJ-'"))
    model = Column(Text, server_default=text("'T7'"))


class FileParentFolder(Base):
    __tablename__ = 'fileParentFolders'

    id = Column(Integer, primary_key=True)
    fullpath = Column(Text, nullable=False, server_default=text("'\\WATSON-BB-OVERS\ServerInternal-01\Transcoded Videos\BB00\'"))
    root = Column(Text, nullable=False, server_default=text("'\\WATSON-BB-OVERS\'"))
    path = Column(Text, nullable=False, server_default=text("'ServerInternal-01\Transcoded Videos\BB00\'"))
    notes = Column(Text)


t_sqlite_sequence = Table(
    'sqlite_sequence', metadata,
    Column('name', NullType),
    Column('seq', NullType)
)


class StaticFileExtension(Base):
    __tablename__ = 'staticFileExtensions'

    extension = Column(Text, primary_key=True, server_default=text("'mp4'"))
    description = Column(Text)
    notes = Column(Text)
    version = Column(Integer, server_default=text("0"))


class Cohort(Base):
    __tablename__ = 'Cohorts'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, server_default=text("'cohort_'"))
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer)
    experiment = Column(ForeignKey('Experiments.id', ondelete='SET NULL'))

    Experiment = relationship('Experiment')


class Subcontext(Base):
    __tablename__ = 'Subcontext'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    parent_context = Column(ForeignKey('Contexts.id'), nullable=False, server_default=text("1"))
    notes = Column(Text)

    Context = relationship('Context')


class TimestampedAnnotation(Base):
    __tablename__ = 'TimestampedAnnotations'

    id = Column(Integer, primary_key=True)
    start_date = Column(Integer)
    end_date = Column(Integer)
    context = Column(ForeignKey('Contexts.id'), server_default=text("1"))
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
    .context = Column(ForeignKey('Contexts.id'), server_default=text("1"))
    Context = relationship('Context')
"""


class ExperimentalConfigurationEvent(Base):
    __tablename__ = 'ExperimentalConfigurationEvents'

    id = Column(Integer, primary_key=True)
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer)
    experiment_id = Column(ForeignKey('Experiments.id'))
    cohort_id = Column(ForeignKey('Cohorts.id'))
    animal_id = Column(ForeignKey('Animals.id'))
    labjack_id = Column(ForeignKey('Labjacks.serial_number'))
    behavioralbox_id = Column(ForeignKey('BehavioralBoxes.numerical_id'))
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
    file_extension = Column(ForeignKey('staticFileExtensions.extension'), nullable=False)
    file_video_folder = Column(ForeignKey('fileParentFolders.id'))
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer)
    duration = Column(Integer)
    behavioral_box_id = Column(ForeignKey('BehavioralBoxes.numerical_id'))
    experiment_id = Column(ForeignKey('Experiments.id'))
    cohort_id = Column(ForeignKey('Cohorts.id'))
    animal_id = Column(ForeignKey('Animals.id'))
    is_original_video = Column(Integer)
    notes = Column(Text)

    animal = relationship('Animal')
    behavioral_box = relationship('BehavioralBox')
    cohort = relationship('Cohort')
    experiment = relationship('Experiment')
    staticFileExtension = relationship('StaticFileExtension')
    fileParentFolder = relationship('FileParentFolder')