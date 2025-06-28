# Auteur
## Overview
Auteur is a web app for organising your writing project.  It allows you to break a project up into sections and then export the whole project as HTML or a PDF.

You can create templates which can then be used a a basis for projects.  A template is really just a project that you mark as being usable as a template.  This allows you to easily clone a project.

Projects can be deleted but not to worry, it is a logical delete so they simply disappear from the "Projects" list.  If you take a look at the "Deleted Projects" list you can undelete the project.  It may be thought of as an organisational tool.

Up to this point Auteur is a single user application but that may change in the future - Flask certainly supports it.

## Technology Choices
A large part of the reason for writing Auteur was to try out an approach to writing a web application that is different to my day to day work.  Additionally I wanted to learn more about using Python to write an application.  

After some investigation and going through the Django tutorials I thought I'd try Flask (thanks Django!)  Seriously, though Django is a great project with superb documentation but it was more than I thought I would need for this project.  Also being a novice Python coder I found Flask was a little more obvious about some of the things it does along with very good documentation.

Anyway, the following excellent software is used / assembled here to create Auteur:
* [Flask](http://flask.pocoo.org/) - a micro framework with lots of handy extensions
  * [Flask-Alchemy](http://flask.pocoo.org/extensions/) - extension to make integration with SQLAlchemy simpler
  * [Flask-Babel](http://flask.pocoo.org/extensions/) - integrate gettext with Flask
  * [Flask-WTForms](http://flask.pocoo.org/extensions/) - handy form validation stuff
* [SQLAlchemy](http://www.sqlalchemy.org/) - an ORM to insulates your application from the implementation details of your database
* [SQLLite](https://sqlite.org/) - a lightweight database, ideal while the application is still single user and while trying out development ideas due to the very low setup overhead
* [Bootstrap](http://getbootstrap.com/) - a nice simple layout framework for the front end.  They provide some sensible options for the look and feel of your components as well
* [jQuery](http://jquery.com/) - smooth out much of the annoyance of dealing with different browsers and the DOM in general
* [CKEditor](http://ckeditor.com/) - any feature you could need from a editor embedded in a web page is here
* [gettext](https://www.gnu.org/s/gettext) - for multi-lingual support
* [WTForms](https://github.com/wtforms/wtforms) - deal with HTML forms in a consistent way throughout your app
* [PyDev](http://www.pydev.org/) in [Eclipse](http://www.eclipse.org/) - makes things easy for the Python newcomer


## Running Auteur
While it's by no means ready for production use it can be run and everything works fine.

Within my PyDev project I just right click on runserver.py and ask it to run.  A new console should pop up showing it listening on 127.0.0.1.  You can now go to 127.0.0.1:5000 in your browser and see a pretty empty page.  If this gives your agrophobia a twinge you could always run the db_data_setup.py script beforehand (or afterwards) to populate the database with some example data.

This is probably a good point to apologise for the error messages.  I'll make them more polite soon.

## Tests
Feel free to run the tests.py unit tests in the top level directory as a pyunit test to see how that works.  I used the Flask and PyUnit testing facilities to allow me to test the views as if they are being called from a browser.  

The in memory form of the SQLLite database is used in the tests for speed and tidyness.  Flipping back if there is a problem is very simple but isn't necessary to decide if your current change can be committed or not.
