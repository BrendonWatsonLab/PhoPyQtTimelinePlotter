# coding: utf-8
from sqlalchemy import Column, ForeignKey, Integer, Table, Text, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.database.entry_models.DatabaseBase import Base, metadata

## Import Statement:
# from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors

class Behavior(Base):
    __tablename__ = 'behaviors'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    parent_group = Column(Integer, ForeignKey('behavior_groups.id'))

    primary_color = Column(Integer, ForeignKey('category_colors.id'), nullable=False, server_default=text("1"))
    secondary_color = Column(Integer, ForeignKey('category_colors.id'), nullable=False, server_default=text("2"))
    note = Column(Text)

    primaryColor = relationship('CategoryColors', foreign_keys=[primary_color])
    secondaryColor = relationship('CategoryColors', foreign_keys=[secondary_color])

    parentGroup = relationship('BehaviorGroup', back_populates="behaviors")


class BehaviorGroup(Base):
    __tablename__ = 'behavior_groups'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    primary_color = Column(Integer, ForeignKey('category_colors.id'), nullable=False, server_default=text("1"))
    secondary_color = Column(Integer, ForeignKey('category_colors.id'), nullable=False, server_default=text("2"))
    note = Column(Text)

    primaryColor = relationship('CategoryColors', foreign_keys=[primary_color])
    secondaryColor = relationship('CategoryColors', foreign_keys=[secondary_color])

    behaviors = relationship("Behavior", order_by=Behavior.id, back_populates="parentGroup")


# A user-assigned color used in the interface
class CategoryColors(Base):
    __tablename__ = 'category_colors'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    colorR = Column(Integer, server_default=text("255"))
    colorG = Column(Integer, server_default=text("255"))
    colorB = Column(Integer, server_default=text("255"))
    note = Column(Text)