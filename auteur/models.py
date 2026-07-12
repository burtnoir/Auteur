"""
Example of the models done in a declarative style.
The foreign key is interesting and the table name variable is needed with this approach.
Created on Apr 25, 2015

@author: sbrooks
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean, DateTime
from datetime import datetime, UTC


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Project(db.Model):
    __tablename__ = 'project'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def short_description(self):
        if len(self.description) > 150:
            return self.description[0:150] + '...'
        return self.description

    def __repr__(self):
        return '<Project %r>' % self.name


class Structure(db.Model):
    __tablename__ = 'structure'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey('structure.id'), nullable=True)
    title: Mapped[str] = mapped_column(String(80))
    displayorder: Mapped[int] = mapped_column(Integer)
    pub_date: Mapped[DateTime] = mapped_column(DateTime)
    children = relationship("Structure",
                            backref=db.backref('parent', remote_side=[id]))

    project_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('project.id'))
    project: Mapped[Project] = relationship('Project',
                                            backref=db.backref('structure', lazy='dynamic'))

    section: Mapped["Section"] = relationship("Section", back_populates="structure", uselist=False, cascade="all, delete-orphan")
    sectionsynopsis: Mapped["SectionSynopsis"] = relationship("SectionSynopsis", back_populates="structure", uselist=False, cascade="all, delete-orphan")
    sectionnotes: Mapped["SectionNotes"] = relationship("SectionNotes", back_populates="structure", uselist=False, cascade="all, delete-orphan")
    sectioncharacters: Mapped["SectionCharacters"] = relationship("SectionCharacters", back_populates="structure", uselist=False, cascade="all, delete-orphan")

    def __init__(self, title, displayorder, project, parent=None, pub_date=None):
        self.title = title
        self.displayorder = displayorder
        if pub_date is None:
            pub_date = datetime.now(UTC)
        self.pub_date = pub_date
        self.project = project
        self.parent = parent

    def __repr__(self):
        return '<Structure %r>' % self.title


class Section(db.Model):
    __tablename__ = 'section'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text)
    pub_date: Mapped[DateTime] = mapped_column(DateTime)

    structure_id: Mapped[int] = mapped_column(Integer, ForeignKey('structure.id'))
    structure: Mapped["Structure"] = relationship(back_populates="section")

    def __init__(self, body, structure, pub_date=None):
        self.body = body
        if pub_date is None:
            pub_date = datetime.now(UTC)
        self.pub_date = pub_date
        self.structure = structure

    def __repr__(self):
        return '<Section %r>' % self.body


class SectionSynopsis(db.Model):
    __tablename__ = 'sectionsynopsis'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text)

    structure_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('structure.id'))
    structure: Mapped["Structure"] = relationship(back_populates="sectionsynopsis")

    def __init__(self, body, structure):
        self.body = body
        self.structure = structure

    def __repr__(self):
        return '<Section Synopsis %r>' % self.body


class SectionNotes(db.Model):
    __tablename__ = 'sectionnotes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text)

    structure_id: Mapped[int] = mapped_column(Integer, ForeignKey('structure.id'))
    structure: Mapped["Structure"] = relationship(back_populates="sectionnotes")

    def __init__(self, body, structure):
        self.body = body
        self.structure = structure

    def __repr__(self):
        return '<Section Notes %r>' % self.body


class SectionCharacters(db.Model):
    __tablename__ = 'sectioncharacters'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text)

    structure_id: Mapped[int] = mapped_column(Integer, ForeignKey('structure.id'))
    structure: Mapped["Structure"] = relationship(back_populates="sectioncharacters")

    def __init__(self, body, structure):
        self.body = body
        self.structure = structure

    def __repr__(self):
        return '<Section Characters %r>' % self.body
