from flask import Flask
from auteur.database import db_session

app = Flask(__name__)

# Configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

import auteur.views