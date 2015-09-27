'''
Example of the models done in a declarative style.
The foreign key is interesting and the table name variable is needed with this approach.
Created on Apr 25, 2015

@author: sbrooks
'''
from auteur import db
from datetime import datetime
    
class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_template = db.Column(db.Boolean)
    is_deleted = db.Column(db.Boolean)

    def __init__(self, name, description, is_template, is_deleted=False):
        self.name = name
        self.description = description
        self.short_description = self.get_short_description()
        self.is_template = is_template
        self.is_deleted = is_deleted
    
    @db.reconstructor
    def init_on_load(self):
        self.short_description = self.get_short_description()
            
    def __repr__(self):
        return '<Project %r>' % self.name
        
    def get_short_description(self):
        if len(self.description) > 150:
            return self.description[0:150] + '...'        
        return self.description


class Structure(db.Model):
    __tablename__ = 'structure'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('structure.id'))
    title = db.Column(db.String(80))
    displayorder = db.Column(db.Integer)
    pub_date = db.Column(db.DateTime)
    children = db.relationship("Structure",
        backref=db.backref('parent', remote_side=[id]))

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project',
        backref=db.backref('structure', lazy='dynamic'))

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


class Section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)

    structure_id = db.Column(db.Integer, db.ForeignKey('structure.id'))
    structure = db.relationship('Structure',
        backref=db.backref('section', lazy='dynamic'))

    def __init__(self, body, structure, pub_date=None):
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.structure = structure

    def __repr__(self):
        return '<Section %r>' % self.body


class SectionSynopsis(db.Model):
    __tablename__ = 'sectionsynopsis'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)

    structure_id = db.Column(db.Integer, db.ForeignKey('structure.id'))
    structure = db.relationship('Structure',
        backref=db.backref('sectionsynopsis', lazy='dynamic'))

    def __init__(self, body, structure, pub_date=None):
        self.body = body
        self.structure = structure

    def __repr__(self):
        return '<Section Synopsis %r>' % self.body


class SectionNotes(db.Model):
    __tablename__ = 'sectionnotes'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)

    structure_id = db.Column(db.Integer, db.ForeignKey('structure.id'))
    structure = db.relationship('Structure',
        backref=db.backref('sectionnotes', lazy='dynamic'))

    def __init__(self, body, structure, pub_date=None):
        self.body = body
        self.structure = structure

    def __repr__(self):
        return '<Section Notes %r>' % self.body