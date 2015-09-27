'''
Created on Apr 25, 2015

@author: sbrooks
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import auteur

# auteur.app.config['DATABASE']
# 'sqlite:////tmp/auteur.db'
engine = create_engine(auteur.app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import auteur.models
    Base.metadata.create_all(bind=engine)
    db_session.commit()
    
def drop_db():
    import auteur.models
    Base.metadata.drop_all(bind=engine)
    db_session.commit()