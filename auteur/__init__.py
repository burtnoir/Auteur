# -*- coding: utf-8 -*-
from flask import Flask
from flask_babel import Babel
from flask_debugtoolbar import DebugToolbarExtension
from flask_wtf.csrf import CsrfProtect
from flask_sqlalchemy import SQLAlchemy

csrf = CsrfProtect()

# create our little application :)
app = Flask(__name__)
app.config.from_object('config')

csrf.init_app(app)
babel = Babel(app)
toolbar = DebugToolbarExtension(app)
db = SQLAlchemy(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    from auteur.database import db_session
    db_session.remove()

import auteur.views