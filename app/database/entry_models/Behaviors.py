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

    def __init__(self,id,name,description,parent_group,primary_color,secondary_color,note):
        self.id = id
        self.name = name
        self.description = description
        self.parent_group = parent_group
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.note = note


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

    def __init__(self,id,name,description,primary_color,secondary_color,note):
        self.id = id
        self.name = name
        self.description = description
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.note = note


# A user-assigned color used in the interface
class CategoryColors(Base):
    __tablename__ = 'category_colors'

    id = Column(Integer, primary_key=True)
    hex_color = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    colorR = Column(Integer, server_default=text("255"))
    colorG = Column(Integer, server_default=text("255"))
    colorB = Column(Integer, server_default=text("255"))
    note = Column(Text)

    def __init__(self,id,hex_color,name,description,colorR,colorG,colorB,note):
        self.id = id
        self.hex_color = hex_color
        self.name = name
        self.description = description
        self.colorR = colorR
        self.colorG = colorG
        self.colorB = colorB
        self.note = note