# Auteur
## Overview
Auteur is a web app for organising your writing project.  It allows you to break a project up into sections and then export the whole project as HTML or a PDF.

You can create templates which can then be used a a basis for projects.  A template is really just a project that you mark as being usable as a template.  This allows you to easily clone a project.

Projects can be deleted but not to worry, it is a logical delete so they simply disappear from the "Projects" list.  If you take a look at the "Deleted Projects" list you can undelete the project.  It may be thought of as an organisational tool.

Up to this point Auteur is a single user application but that may change in the future - Flask certainly supports it.

## Technology Choices
A large part of the reason for writing Auteur was to try out an approach to writing a web application that is different to my day to day work.  Additionally I wanted to learn more about using Python to write an application.  

After some investigation and going through the tutorials I thought I'd try Flask.  Being a novice Python coder I found Flask was obvious in a good way about the things it does along with very good documentation.

Anyway, the following excellent software is used / assembled here to create Auteur:
* [Flask](http://flask.pocoo.org/) - a micro framework with lots of handy extensions
  * [Flask-Alchemy](http://flask.pocoo.org/extensions/) - extension to make integration with SQLAlchemy simpler
  * [Flask-Babel](http://flask.pocoo.org/extensions/) - integrate gettext with Flask
  * [Flask-WTForms](http://flask.pocoo.org/extensions/) - handy form validation stuff
* [SQLAlchemy](http://www.sqlalchemy.org/) - an ORM to insulates your application from the implementation details of your database
* [SQLLite](https://sqlite.org/) - a lightweight database, ideal while the application is still single user and while trying out development ideas due to the very low setup overhead
* [Bootstrap](http://getbootstrap.com/) - a nice simple layout framework for the front end.  They provide some sensible options for the look and feel of your components as well
* [jQuery](http://jquery.com/) - smooth out much of the annoyance of dealing with different browsers and the DOM in general
* [Markdown Text Editor](https://github.com/nezanuha/markdown-text-editor/tree/main) - a markdown editor that's very easy to embed
* [gettext](https://www.gnu.org/s/gettext) - for multi-lingual support
* [WTForms](https://github.com/wtforms/wtforms) - deal with HTML forms in a consistent way throughout your app


## Running Auteur

### Setup
1. Initialize the database:
   ```bash
   uv run python db_data_setup.py
   ```

### Running with Flask
The project uses the Flask application factory pattern. To run it:
```bash
export FLASK_APP=auteur:create_app
export FLASK_DEBUG=true
uv run flask run
```

Alternatively, you can use the legacy `runserver.py`:
```bash
uv run python runserver.py
```

## Tests
Run automated tests using:
```bash
uv run python -m unittest tests/tests.py
```

The in-memory form of the SQLite database is used in the tests for speed and tidiness.
