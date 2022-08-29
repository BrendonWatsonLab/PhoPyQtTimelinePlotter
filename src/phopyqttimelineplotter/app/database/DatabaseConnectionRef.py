# coding: utf-8
from datetime import datetime, timezone, timedelta
from PyQt5.QtCore import Qt, QObject, QEvent, pyqtSignal

import sqlalchemy as db

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker, selectinload, joinedload

# Table Model Generation:
from phopyqttimelineplotter.GUI.Model.AlchemicalModels.qvariantalchemy import String, Integer, Boolean
from phopyqttimelineplotter.GUI.Model.AlchemicalModels.alchemical_model import SqlAlchemyTableModel

# from app.database.SqlAlchemyDatabase import create_connection
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPalette
# from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from app.BehaviorsList import BehaviorsManager, BehaviorInfoOptions

## DATABASE MODELS:
from app.database.entry_models.db_model import Animal, BehavioralBox, Context, Experiment, Labjack, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent, CategoricalDurationLabel

from app.database.entry_models.DatabaseBase import Base, metadata
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors
from app.database.entry_models.db_model import StaticFileExtension, FileParentFolder
from app.database.entry_models.db_model_extension import ExVideoFile

from app.database.utility_functions import *

import sys
import os

from phopyqttimelineplotter.GUI.Model.Videos import VideoInfo


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
        self.enable_debug_printing = True

        self.connect()
        self.initSampleDatabase()

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
                if (self.enable_debug_printing):
                    print("ERROR: Failed to commit changes! Rolling back", e)

                self.rollback() # A constraint failed
                if (self.enable_debug_printing):
                    print("rolled back.")
                
                return False
            except Exception as e:
                print("Other exception! Trying to continue", e)
                return False
        else:
            print("FATAL ERROR: DatabaseConnectionRef has no session!")
            return False

    def rollback(self):
        if self.session:
            try:
              self.session.rollback()
              return True
            except Exception as e:
                print("rollback: Other exception! Trying to continue", e)
                return False
        else:
            print("FATAL ERROR: DatabaseConnectionRef has no session!")
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

    # Called by self.connect() on startup
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
            print("New database built at {0}".format(db_file))

        DBSession = sessionmaker()
        DBSession.bind = engine
        session = DBSession()
        return (engine, DBSession, session)


    ## LOADING:=
    def load_categorical_duration_labels_from_database(self, contextConfigObj):
        if (self.enable_debug_printing):
            print("Loading categorical_duration_labels from database:")
        session = self.get_session()
        currSearchSubcontext = contextConfigObj.get_subcontext()
        # annotations = session.query(CategoricalDurationLabel).options(selectinload(CategoricalDurationLabel.Context)).all()
        records = session.query(CategoricalDurationLabel).filter(CategoricalDurationLabel.Subcontext==currSearchSubcontext).order_by(CategoricalDurationLabel.start_date).all()
        return records

    def load_annotation_events_from_database(self):
        if (self.enable_debug_printing):
            print("Loading annotation events from database:")
        session = self.get_session()
        annotations = session.query(TimestampedAnnotation).options(selectinload(TimestampedAnnotation.Context)).all()
        return annotations

    def load_contexts_from_database(self):
        outputRecordsDict = dict()
        if (self.enable_debug_printing):
            print("Loading contexts from database:")
        session = self.get_session()
        records_list = session.query(Context).options(selectinload(Context.subcontexts)).all()
        for aRecord in records_list:
            outputRecordsDict[aRecord.name] = aRecord
        return outputRecordsDict

    def load_subcontexts_from_database(self):
        if (self.enable_debug_printing):
            print("Loading subcontexts from database:")
        session = self.get_session()
        subcontexts = session.query(Subcontext).all()
        return subcontexts


    def load_colors_from_database(self):
        outputColorsDict = dict()
        if (self.enable_debug_printing):
            print("Loading colors from database:")
        session = self.get_session()
        colors_list = session.query(CategoryColors).all()
        for aColor in colors_list:
            outputColorsDict[aColor.hex_color] = aColor
        return outputColorsDict

    def load_behavior_groups_from_database(self):
        if (self.enable_debug_printing):
            print("Loading behavior_groups from database:")
        session = self.get_session()
        behaviorGroups = session.query(BehaviorGroup).options(selectinload(BehaviorGroup.behaviors)).all()
        return behaviorGroups

    def load_behaviors_from_database(self):
        if (self.enable_debug_printing):
            print("Loading behaviors from database:")
        session = self.get_session()
        behaviors = session.query(Behavior).all()
        return behaviors

    def load_static_file_extensions_from_database(self):
        if (self.enable_debug_printing):
            print("Loading static_file_extensions from database:")
        outputFileExtensionsDict = dict()
        session = self.get_session()
        objs = session.query(StaticFileExtension).all()
        for aRecord in objs:
            outputFileExtensionsDict[aRecord.extension] = aRecord
        return outputFileExtensionsDict

    def load_file_parent_folders_from_database(self, include_video_files=True):
        if (self.enable_debug_printing):
            print("Loading file_parent_folders from database:")
        session = self.get_session()
        if include_video_files:
            objs = session.query(FileParentFolder).options(selectinload(FileParentFolder.videoFiles)).all()
        else:
            objs = session.query(FileParentFolder).all()
        return objs

    def load_video_file_info_from_database(self):
        if (self.enable_debug_printing):
            print("Loading video_file_info from database:")
        session = self.get_session()
        objs = session.query(ExVideoFile).all()
        return objs
    
    

    ## SAVING:
    def save_to_database(self, recordsList, recordTypeName):
        if (self.enable_debug_printing):
            print("Saving {0} records of type <{1}> to database: {2}".format(len(recordsList), recordTypeName, self.get_path()))
        session = self.get_session()
        num_found_records = len(recordsList)
        num_added_records = 0
        num_skipped_records = 0
        for anOutRecord in recordsList:
            try:
                session.add(anOutRecord)
                num_added_records = num_added_records + 1

            except Exception as e:
                print("ERROR: Other exception ({0}) while trying to save {1} records to database! Trying to continue".format(str(e), recordTypeName))
                num_skipped_records = num_skipped_records + 1
                continue

        if (self.enable_debug_printing):
            print('Added ', num_added_records, 'of', num_found_records, recordTypeName, 'records to database.')

        # Save (commit) the changes
        self.commit()

        if (self.enable_debug_printing):
            print("done.")
        return

    def save_contexts_to_database(self, contexts):
        if (self.enable_debug_printing):
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
                print("Other exception! Trying to continue", e)
                num_skipped_records = num_skipped_records + 1
                continue

        # session.add_all(anOutRecord)
        if (self.enable_debug_printing):
            print('Added ', num_added_records, 'of', num_found_records, 'contexts to database.')

        # Save (commit) the changes
        self.commit()

        if (self.enable_debug_printing):
            print("done.")
        return

    def save_annotation_events_to_database(self, annotationEvents):
        if (self.enable_debug_printing):
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
                print("Other exception! Trying to continue", e)
                num_skipped_records = num_skipped_records + 1
                continue

        # session.add_all(anOutRecord)
        if (self.enable_debug_printing):
            print('Added ', num_added_records, 'of', num_found_records, 'annotation events to database.')

        # Save (commit) the changes
        self.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        # session.close()
        if (self.enable_debug_printing):
            print("done.")
        return

    def save_colors_to_database(self, colors):
        if (self.enable_debug_printing):
            print("Saving colors events to database: {0}".format(self.get_path()))
        session = self.get_session()

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

        if (self.enable_debug_printing):
            print('Added ', num_added_records, 'of', num_found_records, 'colors to database.')

        # Save (commit) the changes
        self.commit()

        if (self.enable_debug_printing):
            print("done.")
        return

    def save_behavior_events_to_database(self, behaviors, behavior_groups):
        if (self.enable_debug_printing):
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

        if (self.enable_debug_printing):
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

        if (self.enable_debug_printing):
            print('Preparing to add ', num_added_records, 'of', num_found_records, 'behaviors to database.')

        # Save (commit) the changes
        self.commit()

        if (self.enable_debug_printing):
            print("done.")
        return

    def save_static_file_extensions_to_database(self, static_file_extensions):
        if (self.enable_debug_printing):
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

        if (self.enable_debug_printing):
            print('Added ', num_added_records, 'of', num_found_records, 'static_file_extensions to database.')
        # Save (commit) the changes
        self.commit()

        if (self.enable_debug_printing):
            print("done.")
        return

    def save_file_parent_folders_to_database(self, file_parent_folders):
        if (self.enable_debug_printing):
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

        if (self.enable_debug_printing):
            print('Added ', num_added_records, 'of', num_found_records, 'file_parent_folders to database.')
        # Save (commit) the changes
        self.commit()

        if (self.enable_debug_printing):
            print("done.")
        return

    def save_video_file_info_to_database(self, video_file_info):
        if (self.enable_debug_printing):
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

        if (self.enable_debug_printing):
            print('Added ', num_added_records, 'of', num_found_records, 'video_file_info to database.')
        # Save (commit) the changes
        self.commit()

        if (self.enable_debug_printing):
            print("done.")

        return


    ## Deleting:
    def delete_from_database(self, recordsList):
        if (self.enable_debug_printing):
            print("Deleting {0} records from database: {1}".format(len(recordsList), self.get_path()))
        session = self.get_session()
        num_found_records = len(recordsList)
        num_deleted_records = 0
        num_skipped_records = 0
        for anOutRecord in recordsList:
            recordTypeName = type(anOutRecord)
            try:
                session.delete(anOutRecord)
                num_deleted_records = num_deleted_records + 1

            except Exception as e:
                print("ERROR: Other exception ({0}) while trying to delete record of type {1} to database! Trying to continue".format(str(e), recordTypeName))
                num_skipped_records = num_skipped_records + 1
                continue

        if (self.enable_debug_printing):
            print('Deleted ', num_deleted_records, 'of', num_found_records, recordTypeName, 'records from database.')

        # Save (commit) the changes
        self.commit()

        if (self.enable_debug_printing):
            print("done.")
        return

    ## Model Generation:
    # get_table_model(cls): should work for any record class with a ".getTableMapping()" function defined
    def get_table_model(self, cls, included_columns=None):
        if (self.enable_debug_printing):
            print("get_table_model({0}) from database:".format(str(cls)))
        session = self.get_session()

        all_columns = cls.getTableMapping()
        active_columns = None

        if included_columns is not None:
            active_columns = []

            for aColumnTuple in all_columns:
                column_human_string = aColumnTuple[0]
                column_variable = aColumnTuple[1]
                column_table_id = aColumnTuple[2]

                # Check if the included_columns list includes the human_readable string
                if included_columns.__contains__(column_human_string):
                    active_columns.append(aColumnTuple)
                elif included_columns.__contains__(column_table_id):
                    active_columns.append(aColumnTuple)
                else:
                    print('omitting column: {}'.format(str(column_human_string)))

        else:
            active_columns = all_columns
            

        model = SqlAlchemyTableModel(
            session,
            cls, #sql alchemy mapped object
            active_columns)
        return model

    def get_animal_table_model(self):
        if (self.enable_debug_printing):
            print("get_animal_table_model() from database:")
        session = self.get_session()
        model = SqlAlchemyTableModel(
            session,
            Animal, #sql alchemy mapped object
            Animal.getTableMapping())
        return model

    def initSampleDatabase_ContextsSubcontexts(self):
        print("Creating sample contexts and subcontexts!")
        sampleContexts = [
            Context(None, "Unknown", "sample"),
            Context(None, "Behavior", "sample"),
        ]
        self.save_to_database(sampleContexts, 'Context')

        sampleSubcontexts = [
            Subcontext(None, "Default",1,"sample"),
            Subcontext(None, "Default",2,"sample"),
        ]
        self.save_to_database(sampleSubcontexts, 'Subcontext')

    def initSampleDatabase_Behaviors(self):
        # Creates both the behavior tree and the behaviors database from a set of hard-coded values defined in behaviorsManager
        print("INITIALIZING SAMPLE BEHAVIORS DATABASE")
        behaviorsManager = BehaviorsManager()
        # topLevelNodes = []
        topLeftNodesDict = dict()

        colorsDict = self.load_colors_from_database()
        behaviorGroups = self.load_behavior_groups_from_database()

        # Create new colors if needed
        default_black_color_hex = QColor(0,0,0).name(QColor.HexRgb)
        default_black_color = CategoryColors(None, default_black_color_hex, 'Black', 'Black', 0, 0, 0, None)
        default_white_color_hex = QColor(255,255,255).name(QColor.HexRgb)
        default_white_color = CategoryColors(None, default_white_color_hex,'White', 'White', 255, 255, 255, None)
        defaultColors = [default_black_color,
            default_white_color
        ]

        pending_colors_array = []
        for aPotentialNewColor in defaultColors:
            if (not (aPotentialNewColor.hex_color in colorsDict.keys())):
                pending_colors_array.append(aPotentialNewColor)

        self.save_colors_to_database(pending_colors_array)
        colorsDict = self.load_colors_from_database()

        # For adding to the DB
        behaviorGroupsDBList = []
        behaviorsDBList = []

        # Add the top-level parent nodes
        for (aTypeId, aUniqueBehavior) in enumerate(behaviorsManager.get_unique_behavior_groups()):
            # aNewNode = QTreeWidgetItem([aUniqueBehavior, str(aTypeId), "String C"])
            aNodeColor = behaviorsManager.groups_color_dictionary[aUniqueBehavior]
            # aNewNode.setBackground(0, aNodeColor)
            # topLevelNodes.append(aNewNode)
            

            aNodeColorHexID = aNodeColor.name(QColor.HexRgb)
            if (not (aNodeColorHexID in colorsDict.keys())):
                # If the color is new, add it to the color table in the database
                aDBColor = CategoryColors(None, aNodeColorHexID, aUniqueBehavior, ('Created for ' + aUniqueBehavior), aNodeColor.red(), aNodeColor.green(), aNodeColor.blue(), 'Auto-generated')
                self.save_colors_to_database([aDBColor])
                colorsDict = self.load_colors_from_database()
            else:
                #Else get the existing color
                aDBColor = colorsDict[aNodeColorHexID]
                            
            if (not aDBColor.id):
                print("INVALID COLOR ID!")

            aNewDBNode = BehaviorGroup(None, aUniqueBehavior, aUniqueBehavior, aDBColor.id, default_black_color.id, 'auto')
            behaviorGroupsDBList.append(aNewDBNode)
            topLeftNodesDict[aUniqueBehavior] = (len(behaviorGroupsDBList)-1) # get the index of the added node

        self.save_to_database(behaviorGroupsDBList, 'BehaviorGroup')
        behaviorGroupsDBList = self.load_behavior_groups_from_database()

        # Add the leaf nodes
        for (aSubtypeID, aUniqueLeafBehavior) in enumerate(behaviorsManager.get_unique_behaviors()):
            parentNodeName = behaviorsManager.leaf_to_behavior_groups_dict[aUniqueLeafBehavior]
            parentNodeIndex = topLeftNodesDict[parentNodeName]
            # parentNode = topLevelNodes[parentNodeIndex]
            # if parentNode:
            # found parent
            # aNewNode = QTreeWidgetItem([aUniqueLeafBehavior, "(type: {0}, subtype: {1})".format(str(parentNodeIndex), str(aSubtypeID)), parentNodeName])
            aNodeColor = behaviorsManager.color_dictionary[aUniqueLeafBehavior]
            # aNewNode.setBackground(0, aNodeColor)
            # parentNode.addChild(aNewNode)

            aNodeColorHexID = aNodeColor.name(QColor.HexRgb)
            if (not (aNodeColorHexID in colorsDict.keys())):
                # If the color is new, add it to the color table in the database
                aDBColor = CategoryColors(None, aNodeColorHexID, aUniqueLeafBehavior, ('Created for ' + aUniqueLeafBehavior), aNodeColor.red(), aNodeColor.green(), aNodeColor.blue(), 'Auto-generated')
                self.save_colors_to_database([aDBColor])
                colorsDict = self.load_colors_from_database()
            else:
                #Else get the existing color
                aDBColor = colorsDict[aNodeColorHexID]

            # Get parent node
            parentDBNode = behaviorGroupsDBList[parentNodeIndex]
            if (not parentDBNode):
                print("Couldn't find parent node!")
                parent_node_db_id = None
            else:
                if parentDBNode.id:
                    print("Found parent with index {0}".format(parentDBNode.id))
                    parent_node_db_id = parentDBNode.id
                else:
                    print("couldn't get parent node's .id property, using the index {0}".format(parentNodeIndex + 1))
                    parent_node_db_id = int(parentNodeIndex + 1)

            aNewDBNode = Behavior(None, aUniqueLeafBehavior, aUniqueLeafBehavior, parent_node_db_id, aDBColor.id, default_black_color.id, 'auto')

            behaviorsDBList.append(aNewDBNode)

            # else:
            #     print('Failed to find the parent node with name: ', parentNodeName)
            
        self.save_behavior_events_to_database(behaviorsDBList, behaviorGroupsDBList)
        return 

    ## Defaults/Static Database Setup:
    def initSampleDatabase(self):
        # Need to load all first
        print("Adding sample records if needed...")

        # colorsDict = self.load_colors_from_database()
        # self.behaviorGroups = self.load_behavior_groups_from_database()
        # self.behaviors = self.load_behaviors_from_database()
        # self.fileExtensionDict = self.load_static_file_extensions_from_database()

        # self.contextsDict = self.load_contexts_from_database()
        # self.subcontexts = self.load_subcontexts_from_database()

        # self.annotationDataObjects = self.load_annotation_events_from_database()

        # self.videoFileRecords = self.load_video_file_info_from_database()

        # Sample Contexts
        # if (not ('Behavior' in self.contextsDict.keys())):
        #     Context(None, "Behavior")

        self.initSampleDatabase_Behaviors()
        self.initSampleDatabase_ContextsSubcontexts()

        # Behavioral Boxes
        # sampleAnimals = [(Animal(None, ('Animal_{:04}'.format(i)))) for i in range(0,8)]
        sampleAnimals = []
        for i in range(0,8):
            currNameString = ('Animal_{:04}'.format(i))
            currRecord = Animal()
            currRecord.name = currNameString
            currRecord.notes = 'sample auto'
            sampleAnimals.append(currRecord)

        self.save_to_database(sampleAnimals, 'Animal')

        # sampleBehavioralBoxes = [BehavioralBox(None, 'B{:02}'.format(i)) for i in range(0,16)]
        sampleBehavioralBoxes = []
        for i in range(0,16):
            currNameString = ('B{:02}'.format(i))
            currRecord = BehavioralBox()
            # currRecord.numerical_id = i
            currRecord.name = currNameString
            # currRecord.notes = 'sample auto'
            sampleBehavioralBoxes.append(currRecord)

        self.save_to_database(sampleBehavioralBoxes, 'BehavioralBox')

        # Sample Subcontexts


        # Static File Extensions:
        # Get the appropriate file extension parent
        # currFileExtension = aFoundVideoFile.file_extension[1:].lower()
        # parent_file_extension_obj = None
        # if currFileExtension in self.fileExtensionDict.keys():
        #     parent_file_extension_obj = self.fileExtensionDict[currFileExtension]
        # else:
        #     # Key doesn't exist!
        #     print("extension {0} doesn't exist!".format(currFileExtension))
        #     parent_file_extension_obj = StaticFileExtension("mp4")
        staticFileExtensionObjects = [StaticFileExtension("mp4","MP4 video"),
                StaticFileExtension("mkv","MKV video"),
                StaticFileExtension("avi","AVI video")]
        # Add it to the database
        self.save_static_file_extensions_to_database(staticFileExtensionObjects)



