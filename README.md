#Auteur
##Overview
Auteur is a web app for organising your writing project.  It allows you to break a project up into sections and then export the whole project as HTML or a PDF.

You can create templates which can then be used a a basis for projects.  A template is really just a project that you mark as being usable as a template.  This allows you to easily clone a project.

Projects can be deleted but not to worry, it is a logical delete so they simply disappear from the "Projects" list.  If you take a look at the "Deleted Projects" list you can undelete the project.  It may be thought of as an organisational tool.  

##Technology Choices
A large part of the reason for writing Auteur was to try out an approach to writing a web application that is different to my day to day work.  So after some investigation and going through the Django tutorials I thought I'd try Flask (thanks Django!)  Seriously, though Django is a great project with superb documentation but it was more than I thought I would need for this project.  Also being a novice Python coder I found Flask was a little more obvious about some of the things it does.

Anyway, the following excellent software is used / assembled here to create Auteur:
* Flask - a micro framework with lots of handy extensions
* SQLAlchemy - an ORM to insulates your application from the implementation details of your database
* SQLLite - a lightweight database, ideal while the application is still single user and while trying out development ideas due to the very low setup overhead
* Bootstrap - a nice simple layout framework for the front end.  They provide some sensible options for the look and feel of your components as well
* jQuery - smooth out much of the annoyance of dealing with different browsers and the DOM in general
* CKEditor - any feature you could need from a editor embedded in a web page is here
* gettext - for multi-lingual support
* PyDev in Eclipse - makes things easy for the Python newb


##Running Auteur
While it's by no means ready for production use it can be run and everything works fine.

Within my PyDev project I just right click on runserver.py and ask it to run.  A new console should pop up showing it listening on 127.0.0.1.  You can now go to 127.0.0.1:5000 in your browser and see a pretty empty page.  If this gives your agrophobia a twinge you could always run the db_data_setup.py script beforehand (or afterwards) to populate the database with some example data.

Feel free to run the tests.py unit tests in the top level directory as a pyunit test to see how that works.

This is probably a good point to apologise for the error messages.  I'll make them more polite soon.