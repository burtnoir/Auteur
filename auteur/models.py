"""
Example of the models done in a declarative style.
The foreign key is interesting and the table name variable is needed with this approach.
Created on Apr 25, 2015

@author: sbrooks
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean, DateTime, false
from datetime import datetime, UTC

"""
 The following commands setup a database migration and allow the user to migrate their database instance.
 The first one only needs to be run once to establish a base line to migrate from.  It also needs to mark it
 with flask --app auteur:create_app db stamp head
    flask --app auteur:create_app db init
    flask --app auteur:create_app db stamp head
    flask --app auteur:create_app db migrate -m "initial migration"
    flask --app auteur:create_app db upgrade

 When we make a change to the Models we need to run the second two commands.  One creates the migration script
 and then the second one runs it.  If the migrate doesn't work we might need to update the script created in
 the migrations folder.
"""


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
                            cascade="all, delete-orphan",
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


class Configuration(db.Model):
    """
    A simple global preferences object.  Once we have users then we will have a user preference object that can override the global.
    """
    __tablename__ = 'configuration'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    theme: Mapped[str] = mapped_column(String(50))
    # the server default lets the alembic migration work without needing to update the python script
    # in the migrations directory.
    export_node_titles: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    def __init__(self, theme, export_node_titles=False):
        self.theme = theme
        self.export_node_titles = export_node_titles

    def __repr__(self):
        return '<Configuration %r>' % self.theme