import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
# from db_model import Animal, BehavioralBox, Context, Experiment, Labjack, FileParentFolder, StaticFileExtension, Cohort, Subcontext, TimestampedAnnotation, \
#     ExperimentalConfigurationEvent, VideoFile, Base
from app.database.db_model import Animal, BehavioralBox, Context, Experiment, Labjack, FileParentFolder, StaticFileExtension, Cohort, Subcontext, TimestampedAnnotation, \
    ExperimentalConfigurationEvent

from app.database.entry_models.DatabaseBase import Base, metadata


# Behaviors:
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors

from app.database.db_model_extension import ExVideoFile

from app.database.utility_functions import *

# For convert function
from GUI.Model.PhoDurationEvent_AnnotationComment import *

import sys
import os


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

# Adding objects:
    - when we call "session.add(an_obj)" the instance is said to "pending". 
    Nothing is written until a "flush" occurs.
    When we query that database, all pending info will first be flushed, and then the query will be issued.
    - We can look at pending modified objects with "session.dirty" and new objects with "session.new"
    
# Rolling-back changes:
    - we can roll-back pending changes using session.rollback()



"""












## INITIAL:
def build_new_database(db_file):
    ## TODO:
    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL.
    #Base.metadata.create_all(engine)
    pass

# 'G:\Google Drive\Modern Behavior Box\Results - Data\BehavioralBoxDatabase.db'

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    engine = db.create_engine('sqlite:///' + db_file)
    Base.metadata.bind = engine
    DBSession = sessionmaker()
    DBSession.bind = engine

    try:    
        Base.metadata.create_all(engine)  
    except Exception as e:
        print("Exception while creating the database tables! Trying to continue", e)

    session = DBSession()

    return (engine, DBSession, session)

## LOADING:
def load_annotation_events_from_database(db_file):
    outputAnnotationList = []
    print("Loading annotation events from database:")
    (engine, DBSession, session) = create_connection(db_file=db_file)
    # context = session.query(Context).first()
    # contexts = session.query(Context).all()
    # print(contexts)
    annotations = session.query(TimestampedAnnotation).all()
    return annotations


def load_context_events_from_database(db_file):
    print("Loading context events from database:")
    (engine, DBSession, session) = create_connection(db_file=db_file)
    # context = session.query(Context).first()
    contexts = session.query(Context).all()
    # print(contexts)
    return contexts


    

# def load_video_events_from_database(db_file):
#     outputVideoFileInfoList = []
#     print("Loading video events from database:")
#     (engine, DBSession, session) = create_connection(db_file=db_file)

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
#     (engine, DBSession, session) = create_connection(db_file=db_file)
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

def save_context_events_to_database(db_file, contexts):
    print("Saving context events to database: {0}".format(db_file))
    (engine, DBSession, session) = create_connection(db_file=db_file)
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
    print('Added ', num_added_records, 'of', num_found_records, 'annotation event to database.')

    # Save (commit) the changes
    session.commit()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    session.close()
    print("done.")
    return

def save_annotation_events_to_database(db_file, annotationEvents):
    print("Saving annotation events to database: {0}".format(db_file))
    (engine, DBSession, session) = create_connection(db_file=db_file)
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
    print('Added ', num_added_records, 'of', num_found_records, 'annotation event to database.')

    # Save (commit) the changes
    session.commit()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    session.close()
    print("done.")
    return


## Create Functions
def create_TimestampedAnnotation(start_date, end_date, primary_text, secondary_text, tertiary_text, overflow_text):
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
    return newObj

# Converts an annotation database data object to a GUI element
def convert_TimestampedAnnotation(aTimestampedAnnotationObj):
    end_date = None
    if aTimestampedAnnotationObj.end_date:
        end_date = datetime_from_database(aTimestampedAnnotationObj.end_date)

    newObj = PhoDurationEvent_AnnotationComment(datetime_from_database(aTimestampedAnnotationObj.start_date), end_date,
    aTimestampedAnnotationObj.tertiary_text, aTimestampedAnnotationObj.primary_text, aTimestampedAnnotationObj.secondary_text)
    return newObj

# Updates the provided TimestampedAnnotationObj with the data that was provided from the interface
def modify_TimestampedAnnotation(aTimestampedAnnotationObj, start_date, end_date, title, subtitle, body, overflow_text=''):
    aTimestampedAnnotationObj.primary_text = title
    aTimestampedAnnotationObj.secondary_text = subtitle
    aTimestampedAnnotationObj.tertiary_text = body
    aTimestampedAnnotationObj.overflow_text = ''

    aTimestampedAnnotationObj.start_date = datetime_to_database(start_date)
    if end_date:
        aTimestampedAnnotationObj.end_date = datetime_to_database(end_date)
    else:
        aTimestampedAnnotationObj.end_date = None
    return aTimestampedAnnotationObj



if __name__ == '__main__':
    # load_annotation_events_from_database()
    # load_video_events_from_database()
    found_contexts = load_context_events_from_database('/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db')
    print(found_contexts)
    pass