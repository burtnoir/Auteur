# -*- coding: utf-8 -*-
import click
from flask import Flask, request
from flask_babel import Babel
from flask_bootstrap import Bootstrap5
import os

from flask_migrate import Migrate, upgrade
from .extensions import csrf


# create our little application :)
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'auteur.db'),
    )
    # app.config.from_object('config')
    #
    csrf.init_app(app)
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

    """
     This should make the database available to the blueprints
     The following commands setup a database migration and allow the user to migrate their database instance
        flask --app auteur:create_app db init
        flask --app auteur:create_app db migrate -m "initial migration"
        flask --app auteur:create_app db upgrade
        
     When we make a change to the Models we need to run the second two commands.  One creates the migration script
     and then the second one runs it.  If the migrate doesn't work we might need to update the script created in
     the migrations folder.
    """
    from .models import db
    db.init_app(app)
    migrate = Migrate(app, db)

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
                upgrade()
            click.echo('Database not found - created a new one at %s' % db_path)

    from . import editor
    app.register_blueprint(editor.bp)
    app.add_url_rule('/', endpoint='index')

    return app
