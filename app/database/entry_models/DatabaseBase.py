# coding: utf-8
from sqlalchemy import Column, ForeignKey, Integer, Table, Text, text, MetaData
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

meta = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
      })
Base = declarative_base(metadata=meta)
metadata = Base.metadata

## Import Statement:
# from app.database.entry_models.DatabaseBase import Base, metadata
