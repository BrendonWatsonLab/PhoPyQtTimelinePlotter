import os
import sys

import sqlalchemy as db

# Behaviors:
from phopyqttimelineplotter.app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors
from phopyqttimelineplotter.app.database.entry_models.DatabaseBase import Base, metadata

# from db_model import Animal, BehavioralBox, Context, Experiment, Labjack, FileParentFolder, StaticFileExtension, Cohort, Subcontext, TimestampedAnnotation, \
#     ExperimentalConfigurationEvent, VideoFile, Base
from phopyqttimelineplotter.app.database.entry_models.db_model import (
    Animal,
    BehavioralBox,
    Cohort,
    Context,
    Experiment,
    ExperimentalConfigurationEvent,
    FileParentFolder,
    Labjack,
    StaticFileExtension,
    Subcontext,
    TimestampedAnnotation,
)
from phopyqttimelineplotter.app.database.entry_models.db_model_extension import ExVideoFile
from phopyqttimelineplotter.app.database.utility_functions import *
from sqlalchemy.orm import joinedload, selectinload, sessionmaker

# For convert function
from phopyqttimelineplotter.GUI.Model.Events.PhoDurationEvent_AnnotationComment import *

""" SQLAlchemy: Connects to database backend
"Declarative": system allows us to create python classes that inherent from "Base" class which maintains a catalog of classes and tables that relate to that base.
    - Used in the "db_model.py" file
Within a Base-inheriting class, a "Relationship" object allows retreival of a foreign key (in another table) from the object.
    - The variable with the "Foreign Key" property is still just an "int" or whatever the raw data type is.
    - The "backref" property allows members of the table specified by the foreign key to find all instances in this table that belong to it.
    - The ForeignKey construct constrains the values of a Column to the values present in the named remote column


Boilerplate conversions for datatypes etc isn't built in to SQLAlchemy, but instead you're advised to use "Mixin classes" and helper functions.

"Session": the ORM's "handle" to the database
    - Should be created at application start-up

# Loading Objects:
    - selectinload can be used to "eager-load" objects

# Adding objects:
    - when we call "session.add(an_obj)" the instance is said to "pending".
    Nothing is written until a "flush" occurs.
    When we query that database, all pending info will first be flushed, and then the query will be issued.
    - We can look at pending modified objects with "session.dirty" and new objects with "session.new"

# Rolling-back changes:
    - we can roll-back pending changes using session.rollback()


# Fixing Problems:
    https://docs.sqlalchemy.org/en/13/orm/join_conditions.html



"""


## INITIAL:
def build_new_database(engine):
    ## TODO:
    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL.
    try:
        Base.metadata.create_all(engine)
        return True
    except Exception as e:
        print("Exception while creating the database tables! Trying to continue", e)
        return False


# 'G:\Google Drive\Modern Behavior Box\Results - Data\BehavioralBoxDatabase.db'


def create_connection(db_file, shouldBuildTablesIfNeeded=True):
    """create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    engine = db.create_engine("sqlite:///" + db_file)
    Base.metadata.bind = engine
    if shouldBuildTablesIfNeeded:
        build_new_database(engine)

    DBSession = sessionmaker()
    DBSession.bind = engine
    session = DBSession()
    return (engine, DBSession, session)


## LOADING:
def load_annotation_events_from_database(database_connection_ref):
    outputAnnotationList = []
    print("Loading annotation events from database:")
    session = database_connection_ref.get_session()
    # context = session.query(Context).first()
    # contexts = session.query(Context).all()
    # print(contexts)
    annotations = (
        session.query(TimestampedAnnotation)
        .options(selectinload(TimestampedAnnotation.Context))
        .all()
    )
    return annotations


def load_context_events_from_database(database_connection_ref):
    print("Loading context events from database:")
    session = database_connection_ref.get_session()
    # context = session.query(Context).first()
    contexts = session.query(Context).all()
    # print(contexts)
    return contexts


# def load_video_events_from_database(db_file):
#     outputVideoFileInfoList = []
#     print("Loading video events from database:")
#     session = database_connection_ref.get_session()

#     num_found_files = 0
#     num_added_files = 0
#     num_skipped_files = 0
#     for aVideoRecord in session.query(ExVideoFile).all():
#         currOutputDict = aVideoRecord.get_output_dict()
#         outputVideoFileInfoList.append(currOutputDict)
#         num_found_files = num_found_files + 1

#     print('Found ', num_found_files, 'files in the database.')

#     return outputVideoFileInfoList


## SAVING:
# def save_video_events_to_database(db_file, videoEvents):
#     print("Saving video events to database:")
#     session = database_connection_ref.get_session()
#     num_found_files = len(videoEvents)
#     num_added_files = 0
#     num_skipped_files = 0
#     for aVideoEvent in videoEvents:
#         try:
#             anOutRecord = ExVideoFile.factory(aVideoEvent)
#             session.add(anOutRecord)
#             num_added_files = num_added_files + 1

#         except Exception as e:
#             print(e)
#             print("Other exception! Trying to continue", e)
#             num_skipped_files = num_skipped_files + 1
#             continue

#     # session.add_all(anOutRecord)
#     print('Added ', num_added_files, 'of', num_found_files, 'files to database.')

#     # Save (commit) the changes
#     session.commit()
#     # We can also close the connection if we are done with it.
#     # Just be sure any changes have been committed or they will be lost.
#     session.close()
#     print("done.")
#     return


def save_context_events_to_database(database_connection_ref, contexts):
    print(
        "Saving context events to database: {0}".format(
            database_connection_ref.get_path()
        )
    )
    session = database_connection_ref.get_session()
    num_found_records = len(contexts)
    num_added_records = 0
    num_skipped_records = 0
    for aContext in contexts:
        try:
            anOutRecord = aContext
            session.add(anOutRecord)
            num_added_records = num_added_records + 1

        except Exception as e:
            print(e)
            print("Other exception! Trying to continue", e)
            num_skipped_records = num_skipped_records + 1
            continue

    # session.add_all(anOutRecord)
    print(
        "Added ",
        num_added_records,
        "of",
        num_found_records,
        "annotation event to database.",
    )

    # Save (commit) the changes
    session.commit()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    session.close()
    print("done.")
    return


def save_annotation_events_to_database(database_connection_ref, annotationEvents):
    print(
        "Saving annotation events to database: {0}".format(
            database_connection_ref.get_path()
        )
    )
    session = database_connection_ref.get_session()
    num_found_records = len(annotationEvents)
    num_added_records = 0
    num_skipped_records = 0
    for anAnnotationEvent in annotationEvents:
        try:
            anOutRecord = anAnnotationEvent
            session.add(anOutRecord)
            num_added_records = num_added_records + 1

        except Exception as e:
            print(e)
            print("Other exception! Trying to continue", e)
            num_skipped_records = num_skipped_records + 1
            continue

    # session.add_all(anOutRecord)
    print(
        "Added ",
        num_added_records,
        "of",
        num_found_records,
        "annotation event to database.",
    )

    # Save (commit) the changes
    session.commit()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    session.close()
    print("done.")
    return


## Create Functions
def create_TimestampedAnnotation(
    start_date,
    end_date,
    primary_text,
    secondary_text,
    tertiary_text,
    overflow_text,
    behavioral_box_id,
    experiment_id,
    cohort_id,
    animal_id,
):
    newObj = TimestampedAnnotation()
    # newObj.context = None
    newObj.start_date = datetime_to_database(start_date)
    if end_date:
        newObj.end_date = datetime_to_database(end_date)
    else:
        newObj.end_date = None

    newObj.primary_text = primary_text
    newObj.secondary_text = secondary_text
    newObj.tertiary_text = tertiary_text
    newObj.overflow_text = overflow_text
    newObj.behavioral_box_id = behavioral_box_id
    newObj.experiment_id = experiment_id
    newObj.cohort_id = cohort_id
    newObj.animal_id = animal_id
    return newObj


# Converts an annotation database data object to a GUI element
def convert_TimestampedAnnotation(aTimestampedAnnotationObj, owning_parent):
    end_date = None
    if aTimestampedAnnotationObj.end_date:
        end_date = datetime_from_database(aTimestampedAnnotationObj.end_date)

    newObj = PhoDurationEvent_AnnotationComment(
        datetime_from_database(aTimestampedAnnotationObj.start_date),
        end_date,
        aTimestampedAnnotationObj.tertiary_text,
        aTimestampedAnnotationObj.primary_text,
        aTimestampedAnnotationObj.secondary_text,
        parent=owning_parent,
    )
    return newObj


# Updates the provided TimestampedAnnotationObj with the data that was provided from the interface
def modify_TimestampedAnnotation(
    aTimestampedAnnotationObj,
    start_date,
    end_date,
    title,
    subtitle,
    body,
    overflow_text,
    behavioral_box_id,
    experiment_id,
    cohort_id,
    animal_id,
):
    aTimestampedAnnotationObj.primary_text = title
    aTimestampedAnnotationObj.secondary_text = subtitle
    aTimestampedAnnotationObj.tertiary_text = body
    aTimestampedAnnotationObj.overflow_text = overflow_text
    aTimestampedAnnotationObj.behavioral_box_id = behavioral_box_id
    aTimestampedAnnotationObj.experiment_id = experiment_id
    aTimestampedAnnotationObj.cohort_id = cohort_id
    aTimestampedAnnotationObj.animal_id = animal_id

    aTimestampedAnnotationObj.start_date = datetime_to_database(start_date)
    if end_date:
        aTimestampedAnnotationObj.end_date = datetime_to_database(end_date)
    else:
        aTimestampedAnnotationObj.end_date = None
    return aTimestampedAnnotationObj


# Only updates the startDate
def modify_TimestampedAnnotation_startDate(aTimestampedAnnotationObj, start_date):
    aTimestampedAnnotationObj.start_date = datetime_to_database(start_date)
    activeEndDate = aTimestampedAnnotationObj.end_date
    if activeEndDate:
        if activeEndDate < aTimestampedAnnotationObj.start_date:
            # The start/end dates are reversed! Swap them!
            print("Swapping start/end dates!")
            aTimestampedAnnotationObj.end_date = aTimestampedAnnotationObj.start_date
            aTimestampedAnnotationObj.start_date = activeEndDate

    return aTimestampedAnnotationObj


# Only updates the startDate
def modify_TimestampedAnnotation_endDate(aTimestampedAnnotationObj, end_date):
    if end_date:
        aTimestampedAnnotationObj.end_date = datetime_to_database(end_date)
        activeEndDate = aTimestampedAnnotationObj.end_date
        if activeEndDate:
            if activeEndDate < aTimestampedAnnotationObj.start_date:
                # The start/end dates are reversed! Swap them!
                print("Swapping start/end dates!")
                aTimestampedAnnotationObj.end_date = (
                    aTimestampedAnnotationObj.start_date
                )
                aTimestampedAnnotationObj.start_date = activeEndDate
    else:
        aTimestampedAnnotationObj.end_date = None

    return aTimestampedAnnotationObj


if __name__ == "__main__":
    # load_annotation_events_from_database()
    # load_video_events_from_database()
    database_file_path = (
        "/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db"
    )
    database_connection = DatabaseConnectionRef(database_file_path)
    found_contexts = load_context_events_from_database(database_connection)
    print(found_contexts)
    pass
