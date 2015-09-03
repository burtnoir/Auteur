'''
Example of the models done in a declarative style.
The foreign key is interesting and the table name variable is needed with this approach.
Created on Apr 25, 2015

@author: sbrooks
'''
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from auteur.database import Base
from sqlalchemy import orm
from sqlalchemy.orm import relationship, backref
from datetime import datetime
    
class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(Text)
    is_template = Column(Boolean)
    is_deleted = Column(Boolean)

    def __init__(self, name, description, is_template, is_deleted=False):
        self.name = name
        self.description = description
        self.short_description = self.get_short_description()
        self.is_template = is_template
        self.is_deleted = is_deleted
    
    @orm.reconstructor
    def init_on_load(self):
        self.short_description = self.get_short_description()
            
    def __repr__(self):
        return '<Project %r>' % self.name
        
    def get_short_description(self):
        if len(self.description) > 150:
            return self.description[0:150] + '...'        
        return self.description


class Structure(Base):
    __tablename__ = 'structure'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('structure.id'))
    title = Column(String(80))
    displayorder = Column(Integer)
    pub_date = Column(DateTime)
    children = relationship("Structure",
        backref=backref('parent', remote_side=[id]))

    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project',
        backref=backref('structure', lazy='dynamic'))

    def __init__(self, title, displayorder, project, parent=None, pub_date=None):
        self.title = title
        self.displayorder = displayorder
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.project = project
        self.parent = parent

    def __repr__(self):
        return '<Structure %r>' % self.title


class Section(Base):
    __tablename__ = 'section'
    id = Column(Integer, primary_key=True)
    body = Column(Text)
    pub_date = Column(DateTime)

    structure_id = Column(Integer, ForeignKey('structure.id'))
    structure = relationship('Structure',
        backref=backref('section', lazy='dynamic'))

    def __init__(self, body, structure, pub_date=None):
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.structure = structure

    def __repr__(self):
        return '<Section %r>' % self.body


class SectionSynopsis(Base):
    __tablename__ = 'sectionsynopsis'
    id = Column(Integer, primary_key=True)
    body = Column(Text)

    structure_id = Column(Integer, ForeignKey('structure.id'))
    structure = relationship('Structure',
        backref=backref('sectionsynopsis', lazy='dynamic'))

    def __init__(self, body, structure, pub_date=None):
        self.body = body
        self.structure = structure

    def __repr__(self):
        return '<Section Synopsis %r>' % self.body


class SectionNotes(Base):
    __tablename__ = 'sectionnotes'
    id = Column(Integer, primary_key=True)
    body = Column(Text)

    structure_id = Column(Integer, ForeignKey('structure.id'))
    structure = relationship('Structure',
        backref=backref('sectionnotes', lazy='dynamic'))

    def __init__(self, body, structure, pub_date=None):
        self.body = body
        self.structure = structure

    def __repr__(self):
        return '<Section Notes %r>' % self.body