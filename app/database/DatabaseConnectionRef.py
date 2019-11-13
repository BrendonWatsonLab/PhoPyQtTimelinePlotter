# coding: utf-8
import sys
from datetime import datetime, timezone, timedelta
from PyQt5.QtCore import Qt, QObject, QEvent, pyqtSignal

from app.database.SqlAlchemyDatabase import create_connection

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
        (self.engine, self.DBSession, self.session) = create_connection(db_file=self.db_file)
    
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