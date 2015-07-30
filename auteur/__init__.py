from flask import Flask
from flask_wtf.csrf import CsrfProtect
from flask_debugtoolbar import DebugToolbarExtension

# Configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
DATABASE = 'sqlite:////tmp/auteur.db'

csrf = CsrfProtect()

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

csrf.init_app(app)
toolbar = DebugToolbarExtension(app)

from auteur.database import db_session

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

import auteur.views