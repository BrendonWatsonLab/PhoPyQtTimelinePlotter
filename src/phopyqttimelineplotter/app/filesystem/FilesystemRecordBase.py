import sys
from enum import Enum
from pathlib import Path  # for discover_data_files

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
)

from phopyqttimelineplotter.GUI.Model.Events.PhoDurationEvent import (
    PhoDurationEvent,
    PhoEvent,
)
from phopyqttimelineplotter.GUI.Model.TrackType import TrackType

# FilesystemRecordBase.py
# from phopyqttimelineplotter.app.filesystem.FilesystemRecordBase import FilesystemRecordBase, FilesystemDataEvent_Record, FilesystemLabjackEvent_Record


def discover_data_files(basedir: Path, file_extension=".mat", recursive=True):
    """By default it attempts to find the all *.mat files in the root of this basedir
    Example:
        basedir: Path(r'~/data/Bapun/Day5TwoNovel')
        session_name: 'RatS-Day5TwoNovel-2020-12-04_07-55-09'
    """
    if isinstance(basedir, str):
        basedir = Path(basedir)  # convert to Path object if not already one.
    if recursive:
        glob_pattern = f"**/*{file_extension}"
    else:
        glob_pattern = f"*{file_extension}"
    found_files = sorted(basedir.glob(glob_pattern))
    return found_files  # 'RatS-Day5TwoNovel-2020-12-04_07-55-09'


class DataFileTrackTypeMixin(object):
    @staticmethod
    def get_track_type():
        return TrackType.DataFile


""" FilesystemRecordBase: an attempt to make a "record" like object for events loaded from filesystem files analagous to the records loaded from the database

"""


class FilesystemRecordBase(DataFileTrackTypeMixin, QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)


""" FilesystemDataEvent_Record: for general data events loaded from a data file

"""


class FilesystemDataEvent_Record(FilesystemRecordBase):
    def __init__(
        self,
        start_date,
        end_date,
        variable_name,
        variable_color,
        extended_info_dict,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.start_date = start_date
        self.end_date = end_date
        self.variable_name = variable_name
        self.variable_color = variable_color
        self.extended_info_dict = extended_info_dict

    def get_extended_data(self):
        return self.extended_info_dict

    @staticmethod
    def get_gui_view(aRecord, parent=None):
        currExtraInfoDict = aRecord.extended_info_dict
        outGuiObj = PhoDurationEvent(
            aRecord.start_date,
            aRecord.end_date,
            aRecord.variable_name,
            aRecord.variable_color,
            currExtraInfoDict,
            parent=parent,
        )
        return outGuiObj

    def __getstate__(self):
        odict = self.__dict__.copy()  # copy the dict since we change it
        return odict

    # trying https://stackoverflow.com/questions/48325757/how-to-prevent-a-runtimeerror-when-unpickling-a-qobject
    def __setstate__(self, state):
        # Restore attributes
        self.__dict__.update(state)  # update attributes
        # Call the superclass __init__()
        super(FilesystemDataEvent_Record, self).__init__()

    def to_dict(self):
        return self.__dict__


""" FilesystemLabjackEvent_Record: for labjack events loaded from a labjack data file

"""


class FilesystemLabjackEvent_Record(FilesystemDataEvent_Record):
    def __init__(
        self,
        start_date,
        end_date,
        variable_name,
        variable_color,
        extended_info_dict,
        parent=None,
    ):
        super().__init__(
            start_date,
            end_date,
            variable_name,
            variable_color,
            extended_info_dict,
            parent=parent,
        )
