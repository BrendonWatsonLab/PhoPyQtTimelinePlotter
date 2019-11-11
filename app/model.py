#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta
import json

from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, QObject, pyqtSignal, \
    QModelIndex


class TimestampDelta(timedelta):
    def __new__(cls, *args, **kwargs):
        return super(TimestampDelta, cls).__new__(cls, *args, **kwargs)

    def __str__(self):
        if self.milliseconds == 0:
            return ""
        mm, ss = divmod(self.seconds, 60)
        hh, mm = divmod(mm, 60)
        if self.days:
            hh += self.days * 24
        ms, _ = divmod(self.microseconds, 1000)
        s = "%d:%02d:%02d.%03d" % (hh, mm, ss, ms)
        return s

    @property
    def milliseconds(self):
        ms = self.seconds * 1000000
        if self.microseconds:
            ms += self.microseconds
        if self.days:
            ms += self.days * 24 * 60 * 60 * 100000
        return int(ms/1000)

    @staticmethod
    def from_string(time_string):
        if not time_string:
            return TimestampDelta(milliseconds=0)
        split_time = time_string.split(':', 2)
        split_secs = split_time[2].split('.', 1)
        hours = int(split_time[0])
        if hours < 0:
            raise ValueError
        minutes = int(split_time[1])
        if minutes < 0 or minutes >= 60:
            raise ValueError
        seconds = int(split_secs[0])
        if seconds < 0 or seconds >= 60:
            raise ValueError
        milliseconds = int(split_secs[1])
        if milliseconds < 0 or milliseconds >= 1000:
            raise ValueError
        return TimestampDelta(hours=hours, minutes=minutes, seconds=seconds,
                              milliseconds=milliseconds)

    @staticmethod
    def string_from_int(milliseconds):
        return str(TimestampDelta(milliseconds=milliseconds))


class Timestamp():
    def __init__(self, start_time, end_time, description=None):
        self.start_time = TimestampDelta.from_string(start_time)
        self.end_time = TimestampDelta.from_string(end_time)
        self.description = description

    def get_displayed_start_time(self):
        return str(self.start_time)

    def get_displayed_end_time(self):
        return str(self.end_time)

    def get_string_value_from_index(self, index):
        return str(self.start_time) if index == 0 else str(self.end_time) \
            if index == 1 else self.description

    def get_value_from_index(self, index):
        return self.start_time.milliseconds if index == 0 \
            else self.end_time.milliseconds if index == 1 \
            else self.description

    def set_value_from_index(self, index, value):
        if index == 0:
            self.start_time = value
        elif index == 1:
            self.end_time = value
        elif index == 2:
            self.description = value

    def __repr__(self):
        return json.dumps({
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
            "description": self.description
        }, indent=2)


class TimestampList():
    HEADERS = [
        "Start Time",
        "End Time",
        "Description"
    ]

    def __init__(self, data=[]):
        self.list = []
        for timestamp in data:
            self.list.append(
                Timestamp(
                    timestamp['start_time'],
                    timestamp['end_time'],
                    timestamp['description']
                )
            )

    def append(self, timestamp):
        self.list.append(timestamp)

    def blank_row_index(self):
        for index, entry in enumerate(self.list):
            if not entry.start_time and not entry.end_time and \
               not entry.description:
                return index
        return -1

    def add_blank_row(self):
        self.list.append(Timestamp('', '', ''))

    def remove_row(self, row):
        self.list.pop(row)

    @staticmethod
    def header_at_index(index):
        return TimestampList.HEADERS[index]

    def to_json(self):
        return '[{}]'.format(
            ",\n".join([timestamp.__repr__() for timestamp in self.list]))

    def __len__(self):
        return len(self.list)

    def __getitem__(self, item):
        return self.list[item]

    def __str__(self):
        return str(self.list)

    def __repr__(self):
        return repr(self.list)



class TimestampModel(QAbstractTableModel):
    timeParseError = pyqtSignal(str)

    def __init__(self, input_file_location=None, parent=None):
        super(TimestampModel, self).__init__(parent)
        self.input_file_location = input_file_location
        self.list = TimestampList()

        if input_file_location:
            with open(self.input_file_location, "r+") as input_file:
                self.list = TimestampList(json.load(input_file))

    def rowCount(self, parent=None, *args, **kwargs):
        if parent and parent.isValid():
            return 0
        return len(self.list)

    def columnCount(self, parent=None, *args, **kwargs):
        if parent and parent.isValid():
            return 0
        return 3

    def data(self, index, role=None):
        if not index.isValid():
            return QVariant()
        if role == Qt.UserRole:
            return self.list[index.row()].get_value_from_index(index.column())
        if role != Qt.DisplayRole and role != Qt.EditRole:
            return QVariant()
        return self.list[index.row()].get_string_value_from_index(
            index.column())

    def headerData(self, col, orientation, role=None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.list.header_at_index(col)
        return QVariant()

    def flags(self, index):
        if not index.isValid():
            return None
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, content, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False
        column = index.column()
        try:
            if column == 0 or column == 1:
                content = TimestampDelta.from_string(content)
            self.list[index.row()].set_value_from_index(index.column(), content)
            # In case new values are not valid (e.g. start time that is later
            # than end time), we'll change the *other* value to accommodate
            # the new time
            if column == 0 and self.list[index.row()].end_time < content:
                self.list[index.row()].set_value_from_index(
                    1,
                    TimestampDelta.from_string("")
                )
            if column == 1 and self.list[index.row()].start_time > content:
                self.list[index.row()].set_value_from_index(
                    0,
                    TimestampDelta.from_string("")
                )
            with open(self.input_file_location, "w") as input_file:
                input_file.write(self.list.to_json())
            self.dataChanged.emit(index, index)
            return True
        except (ValueError, IndexError) as err:
            self.timeParseError.emit('Time invalid: ' + content)
            return False

    def insertRows(self, row, count, parent=None, *args, **kwargs):
        if self.list.blank_row_index() != -1:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        self.list.add_blank_row()
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=None, *args, **kwargs):
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            self.list.remove_row(row)
        self.endRemoveRows()
        return True

    def blankRowIndex(self):
        index = self.list.blank_row_index()
        return self.index(index, 0) if index != -1 else QModelIndex()


class ToggleButtonModel(QObject):
    """
    This is the model that controls a ToggleButton. By default, its state is
    True.
    """
    dataChanged = pyqtSignal()
    stateChanged = pyqtSignal(bool)

    def __init__(self, state_map=None, parent=None):
        super(ToggleButtonModel, self).__init__(parent)
        self.state = True
        if state_map:
            self.state_map = state_map
        else:
            self.state_map = {
                True: {
                    "text": None,
                    "icon": None,
                },
                False: {
                    "text": None,
                    "icon": None
                }
            }

    def setStateMap(self, state_map):
        self.state_map = state_map
        self.dataChanged.emit()

    def getText(self, state):
        return self.state_map[state]["text"]

    def getIcon(self, state):
        return self.state_map[state]["icon"]

    def getState(self):
        return self.state

    def setState(self, state):
        self.state = state
        self.stateChanged.emit(self.state)

