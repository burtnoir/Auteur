"""
Created on May 30, 2015

@author: sbrooks
"""
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, TextAreaField, HiddenField, SubmitField
from auteur.models import Project
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import lazy_gettext
from auteur.models import db


class ProjectForm(FlaskForm):
    name = StringField(lazy_gettext('Name'),
                       validators=[DataRequired(message=lazy_gettext('You need to name the project.')),
                                   Length(min=1, max=256, message=lazy_gettext(
                                       'This name is too long - 256 characters should be enough for anyone.'))]
                       )
    description = TextAreaField(lazy_gettext('Description'),
                                validators=[
                                    DataRequired(
                                        message=lazy_gettext('You need to say something about the project.'))
                                ])
    template = SelectField(lazy_gettext('Template'), coerce=int)
    is_template = BooleanField(lazy_gettext('Project Is a Template?'))
    id = HiddenField()
    submit = SubmitField(lazy_gettext('Add Project'))

    def validate_name(self, field):
        """
        This defines an inline validator to check that the project name is unique.
        The naming is important - it must start with the word validate be followed
        by an underscore and then the name of the field.
        """
        current_project_id = self.id.data
        query = db.session.query(db.func.count()).filter(Project.name == field.data)
        if current_project_id:
            query = query.filter(Project.id != int(current_project_id))
        num_same_names = query.scalar()
        if num_same_names > 0:
            raise ValidationError(lazy_gettext('Name already used.  Maybe a writer should try to be more original?'))
