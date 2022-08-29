from pathlib import Path
from datetime import datetime


# For saving to database
def datetime_to_database(python_datetime):
    return int(python_datetime.timestamp() * 1000.0)

def duration_to_database(python_duration):
    return int(python_duration.total_seconds() * 1000.0)


# For loading from database
def datetime_from_database(database_int):
    return datetime.fromtimestamp(float(database_int) / 1000.0)

def duration_from_database(database_int):
    return float(database_int) / 1000.0
