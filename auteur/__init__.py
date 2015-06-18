from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

# Configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
DATABASE = 'sqlite:////tmp/auteur.db'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

toolbar = DebugToolbarExtension(app)

from auteur.database import db_session

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

import auteur.views