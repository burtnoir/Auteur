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
from typing import List
from flask_login import UserMixin

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
 
 SQLite's batch-alter approach means any interrupted migration on this database can leave _alembic_tmp_* debris behind 
 again in the future — if a migration ever fails partway, the same drill applies (check alembic_version, check for 
 stray temp tables, check actual column state before rerunning) and drop / revert them.
"""


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


# Create a User table for all your registered users.
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))
    projects: Mapped[List["Project"]] = relationship()
    checkpoints: Mapped[List["Checkpoint"]] = relationship()

    def get_id(self):
        # This is really important - without it we can log in but
        # the login stuff can't check to see if we are logged in
        # and so the decorators and the current_user don't work.
        return self.email

class Project(db.Model):
    __tablename__ = 'project'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="projects")

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
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": version_id}

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
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": version_id}

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
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": version_id}

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
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": version_id}

    def __init__(self, body, structure):
        self.body = body
        self.structure = structure

    def __repr__(self):
        return '<Section Characters %r>' % self.body


class Checkpoint(db.Model):
    """
    A user-triggered save point for a project. One row per checkpoint;
    the actual content lives in CheckpointSection rows linked to it.
    """
    __tablename__ = 'checkpoint'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('project.id'))
    project: Mapped["Project"] = relationship(
        backref=db.backref('checkpoints', order_by='Checkpoint.created_date.desc()'))

    label: Mapped[str] = mapped_column(String(120))  # e.g. "Before Act 2 rewrite"
    created_date: Mapped[DateTime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    user: Mapped["User"] = relationship(back_populates="checkpoints")

    def __repr__(self):
        return '<Checkpoint %r (%r)>' % (self.label, self.project_id)

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.label
        }


class CheckpointSection(db.Model):
    """
    Snapshot of one structure node's four text bodies at checkpoint time.
    Denormalized (one row holds all four bodies) since they're always
    checkpointed together and it keeps restore simple.

    parent_id/displayorder are snapshotted too (not just a live FK - the
    parent may itself have been deleted since this checkpoint was taken),
    so restore_checkpoint() can recreate a deleted node in its original
    place in the tree rather than just skipping it.
    """
    __tablename__ = 'checkpoint_section'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checkpoint_id: Mapped[int] = mapped_column(Integer, ForeignKey('checkpoint.id'))
    checkpoint: Mapped["Checkpoint"] = relationship(backref=db.backref('sections', cascade='all, delete-orphan'))

    structure_id: Mapped[int] = mapped_column(Integer, ForeignKey('structure.id'))
    # Deliberately NOT a ForeignKey('structure.id') - by the time we come to
    # restore, the parent row this pointed at may itself have been deleted
    # (same reason structure_id above can already point at a gone row).
    parent_id: Mapped[int] = mapped_column(Integer, nullable=True)
    displayorder: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(80))  # snapshot the title too, in case it's renamed later
    section_body: Mapped[str] = mapped_column(Text)
    synopsis_body: Mapped[str] = mapped_column(Text)
    notes_body: Mapped[str] = mapped_column(Text)
    characters_body: Mapped[str] = mapped_column(Text)

    def __repr__(self):
        return '<CheckpointSection structure_id=%r>' % self.structure_id


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