"""
Created on May 30, 2015

@author: sbrooks
"""
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, TextAreaField, HiddenField, SubmitField, EmailField, \
    PasswordField
from auteur.models import Project, Checkpoint
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import lazy_gettext
from auteur.models import db


class RegisterUser(FlaskForm):
    """
    WTFForm to register new users
    """
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginUser(FlaskForm):
    """
    A LoginForm to allow existing users to login
    """
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


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
            raise ValidationError(lazy_gettext('Name already used.  They have to be unique so you can tell them apart.'))

class ConfigurationForm(FlaskForm):
    """
    Show configuration options to the user
    """
    id = HiddenField()
    theme = SelectField(lazy_gettext('Theme'), choices=[('light', lazy_gettext('Light (Default)')), ('dark', lazy_gettext('Dark'))])
    export_node_titles = BooleanField(lazy_gettext(('Export Node Titles?')))
    submit = SubmitField(lazy_gettext('Save'))

class CheckpointForm(FlaskForm):
    """
    Allow the user to enter a label for their checkpoint
    """
    project_id = HiddenField()
    label = StringField(lazy_gettext('Label'),
                       validators=[DataRequired(message=lazy_gettext('You need to name the checkpoint.')),
                                   Length(min=1, max=120, message=lazy_gettext(
                                       'This label can be a maximum of 120 characters.'))]
                       )
    submit = SubmitField(lazy_gettext('Add Checkpoint'))

    def validate_label(self, field):
        """
        Checkpoint labels only need to be unique within a single project,
        not globally - two different projects can both have a "Draft 1"
        checkpoint.
        """
        project_id = self.project_id.data
        query = db.session.query(db.func.count()).filter(
            Checkpoint.project_id == project_id,
            Checkpoint.label == field.data
        )
        num_same_labels = query.scalar()
        if num_same_labels > 0:
            raise ValidationError(lazy_gettext('This label was already used.  They have to be different so you can tell them apart'))

class RestorepointForm(FlaskForm):
    """
    Allow the user to select a checkpoint they want to restore.
    """
    project_id = HiddenField()
    check_point = SelectField(lazy_gettext('Checkpoint'), coerce=int, id="check_point_selection")
    submit = SubmitField(lazy_gettext('Restore Checkpoint'))
