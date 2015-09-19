# -*- coding: utf-8 -*-
from flask import Flask
from flask_wtf.csrf import CsrfProtect
from flask_babel import Babel
from flask_debugtoolbar import DebugToolbarExtension

csrf = CsrfProtect()

# create our little application :)
app = Flask(__name__)
app.config.from_object('config')
#app.config.from_object(__name__)

csrf.init_app(app)
babel = Babel(app)
toolbar = DebugToolbarExtension(app)

from auteur.database import db_session

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

import auteur.views