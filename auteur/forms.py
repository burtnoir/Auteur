'''
Created on May 30, 2015

@author: sbrooks
'''
from flask_wtf import Form
from wtforms import StringField, BooleanField, SelectField, TextAreaField, validators
from auteur.database import db_session
from auteur.models import Project
from wtforms.validators import ValidationError
from sqlalchemy.sql.functions import func

class ProjectForm(Form):
    name = StringField('Name',
                             [
                              validators.Length(min=1, max=256, message='This name is too long - 256 characters should be enough for anyone.'),
                              validators.DataRequired(message='You need to name the project.')
                              ])
    description = TextAreaField('Description',
                         [
                          validators.DataRequired(message='You need to say something about the project.')
                          ])
    template = SelectField('Template', coerce=int)
    is_template = BooleanField("Project Is A Template?")
    
    def validate_project_name(form, field):
        '''
        This defines an inline validator to check that the project name is unique.
        The naming is important - it must start with the word validate.
        '''
        num_same_names = db_session.query(Project.name, func.count(Project.name)).filter_by(name=field.data).scalar()
        if num_same_names > 0:
            raise ValidationError('Name already used.  Maybe a writer should try to be more original?')