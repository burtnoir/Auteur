# -*- coding: utf-8 -*-
import click
from flask import Flask, request
from flask_babel import Babel
from flask_bootstrap import Bootstrap5
import os

from flask_wtf import CSRFProtect


# create our little application :)
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'auteur.db'),
    )
    # app.config.from_object('config')
    #
    csrf = CSRFProtect(app)
    # toolbar = DebugToolbarExtension(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        # This relies on the config.py being in 'instance' - seems to be
        # the right place to put it and it also seems that the instance
        # directory should be outside the application directory so it doesn't
        # have to be committed.
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    def get_locale():
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

    babel = Babel(app, locale_selector=get_locale)
    Bootstrap5(app)

    # This should make the database available to the blueprints
    from .models import db
    db.init_app(app)

    # Check whether the configured SQLite database file already exists.
    # If it doesn't, create it (along with its tables) so the app is ready
    # to use straight away. If it does exist, we simply carry on - the
    # existing data and schema are left untouched.
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    sqlite_prefix = 'sqlite:///'
    if db_uri.startswith(sqlite_prefix):
        db_path = db_uri[len(sqlite_prefix):]
        if not os.path.exists(db_path):
            with app.app_context():
                db.create_all()
            click.echo('Database not found - created a new one at %s' % db_path)

    @app.cli.command('init-db')
    def init_db_command():
        """Create the database tables if they don't already exist.

        This makes sure the SQLite file configured via SQLALCHEMY_DATABASE_URI
        (see instance/config.py) always has the expected schema, without
        touching any data that might already be there.
        Run it with: flask --app auteur:create_app init-db
        """
        with app.app_context():
            db.create_all()
        click.echo('Initialized the database at %s' % app.config['SQLALCHEMY_DATABASE_URI'])

    from . import editor
    app.register_blueprint(editor.bp)
    app.add_url_rule('/', endpoint='index')

    return app
