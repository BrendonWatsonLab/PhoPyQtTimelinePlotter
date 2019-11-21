#!/usr/bin/env python2
#-*- coding=utf-8 -*-
# © 2013 Mark Harviston, BSD License
from __future__ import absolute_import, unicode_literals, print_function
"""
SQLAlchemy types for dealing with QVariants & various QTypes (like QString)
"""

import datetime

from PyQt5.QtCore import QVariant
from sqlalchemy import types


def gen_process_bind_param(pytype, toqtype, self, value, dialect):
    if value is None:
        return None
    elif isinstance(value, QVariant):
        return pytype(toqtype(value))
    elif not isinstance(value, pytype):
        return pytype(value)
    else:
        return value


class Integer(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        return gen_process_bind_param(
            long, lambda value: value.toLongLong(),
            self, value, dialect)


class Boolean(types.TypeDecorator):
    impl = types.Boolean

    def process_bind_param(self, value, dialect):
        return gen_process_bind_param(
            bool, lambda value: value.toBool(),
            self, value, dialect)


class String(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        return gen_process_bind_param(
            unicode, lambda value: value.toString(),
            self, value, dialect)


class Enum(types.TypeDecorator):
    impl = types.Enum

    def process_bind_param(self, value, dialect):
        return gen_process_bind_param(
            unicode, lambda value: value.toString(),
            self, value, dialect)


class DateTime(types.DateTime):
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        return gen_process_bind_param(
            datetime.datetime, lambda value: value.toDateTime(),
            self, value, dialect)
