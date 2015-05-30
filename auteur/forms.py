'''
Created on May 30, 2015

@author: sbrooks
'''
from wtforms import Form, TextField, validators

class AddProject(Form):
    project_name = TextField('New Project Name',
                             [
                              validators.Length(min=1, max=256),
                              validators.Required()
                              ])
