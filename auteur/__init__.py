# -*- coding: utf-8 -*-
import click
from flask import Flask, request, redirect, render_template, flash, url_for
from flask_babel import Babel
from flask_bootstrap import Bootstrap5
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
import os

from flask_migrate import Migrate, upgrade
from .extensions import csrf
from .forms import LoginUser, RegisterUser
from werkzeug.security import generate_password_hash, check_password_hash

from .models import Configuration, User


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

    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)

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

    def admin_only(function):
        # Decorator function to make sure that anyone calling an endpoint decorated by this
        # is logged in as the admin user - currently defined by an id of 1 - bit simple but it
        # shows a way to do it.
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if current_user.id == 1:
                return function(*args, **kwargs)
            else:
                abort(403)

        return decorated_function

    @login_manager.user_loader
    def load_user(user_email):
        return db.session.scalars(db.select(User).where(User.email == user_email)).first()

    # Register a user and use Werkzeug to hash the user's password.
    @app.route('/register', methods=['POST', 'GET'])
    def register():
        form = RegisterUser()
        if form.validate_on_submit():
            if load_user(form.email.data):
                flash('This email address is already registered, please login instead of registering.', 'error')
                return redirect(url_for('login'))
            user = User()
            user.name = form.name.data
            user.email = form.email.data
            user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            db.session.add(user)
            db.session.commit()

            # Log the user in via the login manager
            login_user(user)
            return redirect(url_for('editor.get_project_list'))
        config = Configuration.query.filter_by(id=1).first()
        return render_template("register.jinja", form=form, config=config)

    # Retrieve a user from the database based on their email.
    @app.route('/login', methods=['POST', 'GET'])
    def login():
        form = LoginUser()
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            user = load_user(email)
            # Check everything is OK before passing the user on to the secrets page.
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('editor.get_project_list'))
            # If this is a POST request but there's a problem with the login credentials
            # show a message and offer the login page again.
            flash('The email address and password combination is not recognised.', 'error')
            return redirect(url_for('login'))
        config = Configuration.query.filter_by(id=1).first()
        return render_template("login.jinja", form=form, config=config)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('editor.get_project_list'))

    from . import editor
    app.register_blueprint(editor.bp)
    app.add_url_rule('/', endpoint='index')

    return app
