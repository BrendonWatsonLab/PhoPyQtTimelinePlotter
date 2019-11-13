# coding: utf-8
from datetime import datetime, timezone, timedelta
from PyQt5.QtCore import Qt, QObject, QEvent, pyqtSignal

import sqlalchemy as db
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, selectinload, joinedload

# from app.database.SqlAlchemyDatabase import create_connection


## DATABASE MODELS:
from app.database.db_model import Animal, BehavioralBox, Context, Experiment, Labjack, FileParentFolder, StaticFileExtension, Cohort, Subcontext, TimestampedAnnotation, \
    ExperimentalConfigurationEvent

from app.database.entry_models.DatabaseBase import Base, metadata
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors
from app.database.db_model_extension import ExVideoFile

from app.database.utility_functions import *

import sys
import os


"""
An open reference to the databse shared by the different windows
"""
class DatabaseConnectionRef(QObject):
    def __init__(self, db_file):
        super(DatabaseConnectionRef, self).__init__(None)
        self.db_file = db_file
        self.engine = None
        self.session = None
        self.DBSession = None

        self.connect()

    def connect(self):
        (self.engine, self.DBSession, self.session) = self.create_connection(db_file=self.db_file, shouldBuildTablesIfNeeded=True)
    
    def commit(self):
        if self.session:
            self.session.commit()

    def close(self):
        if self.session:
            self.session.close()

    ## Getters:
    
    def get_session(self):
        return self.session

    def get_engine(self):
        return self.engine

    def get_path(self):
        return self.db_file

    ## INITIAL:
    def build_new_database(self, engine):
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

    def create_connection(self, db_file, shouldBuildTablesIfNeeded=True):
        """ create a database connection to the SQLite database
            specified by the db_file
        :param db_file: database file
        :return: Connection object or None
        """
        engine = db.create_engine('sqlite:///' + db_file)
        Base.metadata.bind = engine
        if shouldBuildTablesIfNeeded:
            self.build_new_database(engine)

        DBSession = sessionmaker()
        DBSession.bind = engine
        session = DBSession()
        return (engine, DBSession, session)


    ## LOADING:=
    def load_annotation_events_from_database(self):
        outputAnnotationList = []
        print("Loading annotation events from database:")
        session = self.get_session()
        # context = session.query(Context).first()
        # contexts = session.query(Context).all()
        # print(contexts)
        annotations = session.query(TimestampedAnnotation).options(selectinload(TimestampedAnnotation.Context)).all()
        return annotations

    def load_context_events_from_database(self):
        print("Loading context events from database:")
        session = self.get_session()
        # context = session.query(Context).first()
        contexts = session.query(Context).all()
        # print(contexts)
        return contexts

    def load_colors_from_database(self):
        outputColorsDict = dict()
        print("Loading colors from database:")
        session = self.get_session()
        # context = session.query(Context).first()
        # contexts = session.query(Context).all()
        # print(contexts)
        colors_list = session.query(CategoryColors).all()
        for aColor in colors_list:
            outputColorsDict[aColor.hex_color] = aColor
        return outputColorsDict



    ## SAVING:
    def save_context_events_to_database(self, contexts):
        print("Saving context events to database: {0}".format(self.get_path()))
        session = self.get_session()
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
        # session.close()
        print("done.")
        return

    def save_annotation_events_to_database(self, annotationEvents):
        print("Saving annotation events to database: {0}".format(self.get_path()))
        session = self.get_session()
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
        # session.close()
        print("done.")
        return

    def save_colors_to_database(self, colors):
        print("Saving colors events to database: {0}".format(self.get_path()))
        session = self.get_session()

        # Behavior Groups:
        num_found_records = len(colors)
        num_added_records = 0
        num_skipped_records = 0
        for anOutRecord in colors:
            try:
                session.add(anOutRecord)
                num_added_records = num_added_records + 1

            except Exception as e:
                print("Other exception! Trying to continue", e)
                num_skipped_records = num_skipped_records + 1
                continue

        print('Added ', num_added_records, 'of', num_found_records, 'colors to database.')
        # Save (commit) the changes
        session.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        # session.close()
        print("done.")
        return

    def save_behavior_events_to_database(self, behaviors, behavior_groups):
        print("Saving behavior/behavior_group events to database: {0}".format(self.get_path()))
        session = self.get_session()

        # Behavior Groups:
        num_found_records = len(behavior_groups)
        num_added_records = 0
        num_skipped_records = 0
        for anOutRecord in behavior_groups:
            try:
                session.add(anOutRecord)
                num_added_records = num_added_records + 1

            except Exception as e:
                print("Other exception! Trying to continue", e)
                num_skipped_records = num_skipped_records + 1
                continue

        print('Preparing to add ', num_added_records, 'of', num_found_records, 'behavior_groups to database.')

        # Behaviors:
        num_found_records = len(behaviors)
        num_added_records = 0
        num_skipped_records = 0
        for anOutRecord in behaviors:
            try:
                session.add(anOutRecord)
                num_added_records = num_added_records + 1

            except Exception as e:
                print("Other exception! Trying to continue", e)
                num_skipped_records = num_skipped_records + 1
                continue

        print('Preparing to add ', num_added_records, 'of', num_found_records, 'behaviors to database.')



        # Save (commit) the changes
        try:
            # See https://stackoverflow.com/questions/52075642/how-to-handle-unique-data-in-sqlalchemy-flask-pyhon
            session.commit()
            print("Committed changes!")
        except IntegrityError as e:
            session.rollback() # A constraint failed
            print("ERROR: Failed to commit changes! Rolling back", e)

        except Exception as e:
                print("Other exception! Trying to continue", e)
                
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        # session.close()
        print("done.")
        return

    
    