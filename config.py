# -*- coding: utf-8 -*-
# Configuration
import os
basedir = os.path.abspath(os.path.dirname(__file__))
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'auteur.db')
WTF_CSRF_ENABLED = True
DEBUG_TB_INTERCEPT_REDIRECTS = False
LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Francais'
}
