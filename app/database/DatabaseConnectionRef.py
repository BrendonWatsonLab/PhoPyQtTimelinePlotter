# coding: utf-8
from datetime import datetime, timezone, timedelta
from PyQt5.QtCore import Qt, QObject, QEvent, pyqtSignal

import sqlalchemy as db
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, selectinload, joinedload

# Table Model Generation:
from GUI.Model.AlchemicalModels.qvariantalchemy import String, Integer, Boolean
from GUI.Model.AlchemicalModels.alchemical_model import SqlAlchemyTableModel

# from app.database.SqlAlchemyDatabase import create_connection


## DATABASE MODELS:
from app.database.entry_models.db_model import Animal, BehavioralBox, Context, Experiment, Labjack, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent

from app.database.entry_models.DatabaseBase import Base, metadata
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors
from app.database.entry_models.db_model import StaticFileExtension, FileParentFolder
from app.database.entry_models.db_model_extension import ExVideoFile

from app.database.utility_functions import *

import sys
import os

from GUI.Model.Videos import VideoInfo


class DatabasePendingItemsState(QObject):
    def __init__(self, created_count, modified_count):
        super(DatabasePendingItemsState, self).__init__(None)
        self.created_count = created_count
        self.modified_count = modified_count

    def get_created_count(self):
        return self.created_count

    def get_modified_count(self):
        return self.modified_count

    def get_total_pending(self):
        return (self.created_count + self.modified_count)

    def has_pending(self):
        return (self.get_total_pending() > 0)

    def __str__(self):
        return '(created: {0}, modified: {1}, total: {2})'.format(self.created_count, self.modified_count, self.get_total_pending())


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
        self.enable_debug_printing = False

        self.connect()

    def connect(self):
        (self.engine, self.DBSession, self.session) = self.create_connection(db_file=self.db_file, shouldBuildTablesIfNeeded=True)
    
    def commit(self):
        if self.session:
            try:
                # See https://stackoverflow.com/questions/52075642/how-to-handle-unique-data-in-sqlalchemy-flask-pyhon
                self.session.commit()
                if (self.enable_debug_printing):
                    print("Committed changes!")
                return True
            except IntegrityError as e:
                self.session.rollback() # A constraint failed
                if (self.enable_debug_printing):
                    print("ERROR: Failed to commit changes! Rolling back", e)
                return False
            except Exception as e:
                print("Other exception! Trying to continue", e)
                return False


    def rollback(self):
        if self.session:
            try:
              self.session.rollback()
              return True
            except Exception as e:
                print("rollback: Other exception! Trying to continue", e)
                return False
        return False


    # Gets the modified records
    def get_pending_modified(self):
        if self.session:
            try:
              return self.session.dirty
            except Exception as e:
                print("get_pending_modified: Other exception! Trying to continue", e)
                return []
    
        return []

    # Gets the new records
    def get_pending_new(self):
        if self.session:
            try:
              return self.session.new
            except Exception as e:
                print("get_pending_new: Other exception! Trying to continue", e)
                return []
        
        return []

    # Gets the pending record counts as a DatabasePendingItemsState object (new, modified, total)
    def get_pending_counts(self):
        pending_new = self.get_pending_new()
        pending_modified = self.get_pending_modified()

        output = DatabasePendingItemsState(len(pending_new), len(pending_modified))

        # return (len(pending_new), len(pending_modified), (len(pending_new) + len(pending_modified)))
        return output


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
        print("Loading annotation events from database:")
        session = self.get_session()
        annotations = session.query(TimestampedAnnotation).options(selectinload(TimestampedAnnotation.Context)).all()
        return annotations

    def load_contexts_from_database(self):
        print("Loading contexts from database:")
        session = self.get_session()
        contexts = session.query(Context).all()
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

    def load_behavior_groups_from_database(self):
        print("Loading behavior_groups from database:")
        session = self.get_session()
        behaviorGroups = session.query(BehaviorGroup).options(selectinload(BehaviorGroup.behaviors)).all()
        return behaviorGroups

    def load_behaviors_from_database(self):
        print("Loading behaviors from database:")
        session = self.get_session()
        behaviors = session.query(Behavior).all()
        return behaviors

    def load_static_file_extensions_from_database(self):
        print("Loading static_file_extensions from database:")
        outputFileExtensionsDict = dict()
        session = self.get_session()
        objs = session.query(StaticFileExtension).all()
        for aRecord in objs:
            outputFileExtensionsDict[aRecord.extension] = aRecord
        return outputFileExtensionsDict

    def load_file_parent_folders_from_database(self, include_video_files=True):
        print("Loading file_parent_folders from database:")
        session = self.get_session()
        if include_video_files:
            objs = session.query(FileParentFolder).options(selectinload(FileParentFolder.videoFiles)).all()
        else:
            objs = session.query(FileParentFolder).all()
        return objs

    def load_video_file_info_from_database(self):
        print("Loading video_file_info from database:")
        session = self.get_session()
        objs = session.query(ExVideoFile).all()
        return objs
    
    

    ## SAVING:
    def save_contexts_to_database(self, contexts):
        print("Saving contexts to database: {0}".format(self.get_path()))
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
        print('Added ', num_added_records, 'of', num_found_records, 'contexts to database.')

        # Save (commit) the changes
        self.commit()
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
        print('Added ', num_added_records, 'of', num_found_records, 'annotation events to database.')

        # Save (commit) the changes
        self.commit()
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
        self.commit()
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
        self.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        # session.close()
        print("done.")
        return

    def save_static_file_extensions_to_database(self, static_file_extensions):
        print("Saving static_file_extensions to database: {0}".format(self.get_path()))
        session = self.get_session()

        # Behavior Groups:
        num_found_records = len(static_file_extensions)
        num_added_records = 0
        num_skipped_records = 0
        for anOutRecord in static_file_extensions:
            try:
                session.add(anOutRecord)
                num_added_records = num_added_records + 1

            except Exception as e:
                print("Other exception! Trying to continue", e)
                num_skipped_records = num_skipped_records + 1
                continue

        print('Added ', num_added_records, 'of', num_found_records, 'static_file_extensions to database.')
        # Save (commit) the changes
        self.commit()
        print("done.")
        return

    def save_file_parent_folders_to_database(self, file_parent_folders):
        print("Saving file_parent_folders to database: {0}".format(self.get_path()))
        session = self.get_session()

        # Behavior Groups:
        num_found_records = len(file_parent_folders)
        num_added_records = 0
        num_skipped_records = 0
        for anOutRecord in file_parent_folders:
            try:
                session.add(anOutRecord)
                num_added_records = num_added_records + 1

            except Exception as e:
                print("Other exception! Trying to continue", e)
                num_skipped_records = num_skipped_records + 1
                continue

        print('Added ', num_added_records, 'of', num_found_records, 'file_parent_folders to database.')
        # Save (commit) the changes
        self.commit()
        print("done.")
        return

    def save_video_file_info_to_database(self, video_file_info):
        print("Saving video_file_info to database: {0}".format(self.get_path()))
        session = self.get_session()

        # Behavior Groups:
        num_found_records = len(video_file_info)
        num_added_records = 0
        num_skipped_records = 0
        for anOutRecord in video_file_info:
            try:
                session.add(anOutRecord)
                num_added_records = num_added_records + 1

            except Exception as e:
                print("Other exception! Trying to continue", e)
                num_skipped_records = num_skipped_records + 1
                continue

        print('Added ', num_added_records, 'of', num_found_records, 'video_file_info to database.')
        # Save (commit) the changes
        self.commit()
        print("done.")
        return

    ## Model Generation:
    def get_animal_table_model(self):
        print("get_animal_table_model() from database:")
        session = self.get_session()
        model = SqlAlchemyTableModel(
            session,
            Animal, #sql alchemy mapped object
            Animal.getTableMapping())
        return model