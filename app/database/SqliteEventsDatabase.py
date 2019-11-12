import sqlite3
from sqlite3 import Error
from pathlib import Path
from datetime import datetime

from GUI.Model.Videos import *

# def create_connection(db_file='G:\Google Drive\Modern Behavior Box\Results - Data\BehavioralBoxDatabase.db'):
def create_connection(db_file='/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db'):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def save_video_events_to_database(videoEvents):
    print("Saving video events to database:")
    conn = create_connection()
    num_found_files = len(videoEvents)
    num_added_files = 0
    num_skipped_files = 0
    for aVideoEvent in videoEvents:
        aFullPath = aVideoEvent.extended_data['fullpath']
        aFullParentPath = str(aVideoEvent.extended_data['parent_path']) # The parent path
        aFullName = aVideoEvent.name # The full name including extension
        aBaseName = aVideoEvent.extended_data['base_name'] # Excluding the period and extension
        anExtension = aVideoEvent.extended_data['file_extension'][1:] # the file extension excluding the period
        if (not aVideoEvent.extended_data['behavioral_box_id'] is None):
            aBBID = aVideoEvent.extended_data['behavioral_box_id']+1 # Add one to get a valid index
        else:
            aBBID = 1

        if (not aVideoEvent.extended_data['is_deeplabcut_labeled_video'] is None):
            is_deeplabcut_labeled_video = aVideoEvent.extended_data['is_deeplabcut_labeled_video']
            is_original_video = (not is_deeplabcut_labeled_video)
        else:
            is_deeplabcut_labeled_video = None
            is_original_video = None # We know nothing about whether it is an original video

        anExperimentID = 1
        aCohortID = 1
        anAnimalID = 3
        notes = ''
        startTime = int(aVideoEvent.startTime.timestamp()*1000.0)
        endTime = int(aVideoEvent.endTime.timestamp()*1000.0)
        duration = int(aVideoEvent.computeDuration().total_seconds()*1000.0)
        #anOutRecord = (None, aFullName, aBaseName, anExtension, aFullParentPath, startTime, endTime, duration, aBBID, anExperimentID, aCohortID, anAnimalID, notes)
        anOutRecord = (aFullName, aBaseName, anExtension, aFullParentPath, startTime, endTime, duration, aBBID, anExperimentID, aCohortID, anAnimalID, is_original_video, notes)
        try:
            conn.execute('INSERT INTO VideoFile (file_fullname, file_basename, file_extension, file_video_folder, start_date, end_date, duration, behavioral_box_id, experiment_id, cohort_id, animal_id, is_original_video, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', anOutRecord)
            conn.commit()
            num_added_files = num_added_files + 1

        except sqlite3.IntegrityError:
            print("Failed to add record! Continuing")
            num_skipped_files = num_skipped_files + 1
            continue
        except Exception as e:
            print(e)
            print("Other exception! Trying to continue", e)
            num_skipped_files = num_skipped_files + 1
            continue

    print('Added ', num_added_files, 'of', num_found_files, 'files to database.')

    # Save (commit) the changes
    conn.commit()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()
    print("done.")
    return


def load_video_events_from_database(as_videoInfo_objects=False):
    """
    as_videoInfo_objects: if true, outputs "VideoInfo" objects instead of an array of dictionaries.
    """
    outputVideoFileInfoList = []
    print("Loading video events from database:")
    conn = create_connection()
    # cur = conn.cursor()
    num_found_files = 0
    num_added_files = 0
    num_skipped_files = 0
    for aVideoRecord in conn.execute('SELECT * FROM VideoFile ORDER BY start_date'):
        (aRecordID, aFullName, aBaseName, anExtension, aFullParentPath, startTimeNum, endTimeNum, durationNum, aBBID, anExperimentID, aCohortID, anAnimalID, is_original_video, notes) = aVideoRecord
        startTime = datetime.fromtimestamp(float(startTimeNum) / 1000.0)
        endTime = datetime.fromtimestamp(float(endTimeNum) / 1000.0)
        duration = float(durationNum) / 1000.0
        anExtension = '.' + anExtension # Add the period back on
        entries = Path(aFullParentPath)
        # aFullPath = entries.joinpath(aFullName).resolve(strict=True)
        aFullPath = entries.joinpath(aFullName).resolve(strict=False)

        # Allow being undecided as to whether a video is an original or not
        if (is_original_video is None):
            is_deeplabcut_labeled_video = None
        else:
            is_deeplabcut_labeled_video = (not is_original_video)

        ## TODO: Decide whether to port these changes back to PhoPythonVideoFileParser proj
        # DO I want to do ".replace(tzinfo=None)" at this stage?
        if as_videoInfo_objects:
            newExperimentContextInfoObj = ExperimentContextInfo(-1, aBBID, anExperimentID, aCohortID, anAnimalID, notes)
            newVideoInfoObj = VideoInfo(aFullName, aBaseName, anExtension, aFullParentPath, startTime.replace(tzinfo=None), endTime.replace(tzinfo=None), duration, is_original_video, newExperimentContextInfoObj)
            outputVideoFileInfoList.append(newVideoInfoObj)

        else:
            currProperties = {'duration': duration}
            extendedProperties = {'behavioral_box_id': aBBID}
            currOutputDict = {'base_name': aBaseName, 'file_fullname': aFullName, 'file_extension': anExtension, 'parent_path': aFullParentPath, 'path': aFullPath, 'parsed_date': startTime, 'computed_end_date': endTime, 'is_deeplabcut_labeled_video': is_deeplabcut_labeled_video, 'properties': currProperties, 'extended_properties': extendedProperties}
            outputVideoFileInfoList.append(currOutputDict)

        num_found_files = num_found_files + 1

    print('Found ', num_found_files, 'files in the database.')

    return outputVideoFileInfoList

