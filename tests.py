'''
Created on May 28, 2015

@author: sbrooks
'''
import unittest
from auteur import app, db
from auteur.models import Project
from flask import json

#import os
#from config import basedir

class ProjectTestCase(unittest.TestCase):

    def setUp(self):
        #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        

    def test_empty_db(self):
        rv = self.app.get('/')
        self.assertIn('No entries here so far', rv.data)


    def test_project(self):
        rv = self.app.post('/add_project', data=dict(
            name=''
        ), follow_redirects=True)
        self.assertIn('You need to name the project.', rv.data)
        
        rv = self.app.post('/add_project', data=dict(
            name='Automated Test Project'
        ), follow_redirects=True)
        self.assertIn('You need to say something about the project.', rv.data)

        rv = self.app.post('/add_project', data=dict(
                                                     name='',
                                                     description='Automated Test Project'
        ), follow_redirects=True)
        self.assertIn('You need to name the project.', rv.data)
        
        rv = self.app.post('/add_project', data=dict(
            name='Automated Test Project',
            description='Automated Test Project Description goes here!',
            is_template=False,
            template=0
        ), follow_redirects=True)
        self.assertIn('Automated Test Project', rv.data)
        self.assertIn('Automated Test Project Description goes here!', rv.data)
        
        rv = self.app.post('/add_project', data=dict(
            name='Automated Test Project',
            description='Automated Test Project Description goes here! Description is different.',
            is_template=False,
            template=0
        ), follow_redirects=True)
        self.assertIn('Name already used.  Maybe a writer should try to be more original?', rv.data)
    

    def test_nodes(self):
        # Add a project so there is something to hang our node tests off.
        self.app.post('/add_project', data=dict(
            name='Node Test Project',
            description='Automated Test Project for Checking Node Behaviour',
            is_template=False,
            template=0
        ))
        
        # Add a new node to the root node of our project.
        project_id = Project.query.with_entities(Project.id).filter(Project.name=='Node Test Project').first()
        rv = self.app.post('/add_node/' + str(project_id[0]), 
                           headers=[('X-Requested-With', 'XMLHttpRequest')], 
                           content_type='application/json', 
                           data=json.dumps(dict(pos='last', parent=1))
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Section was added.")
        # Update it
        node_id = data['id']
        rv = self.app.post('/update_node', 
                           headers=[('X-Requested-With', 'XMLHttpRequest')], 
                           content_type='application/json', 
                           data=json.dumps(dict(id=node_id, text='Changed Node Text'))
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Section was updated.")
        # And then delete it.
        rv = self.app.post('/delete_node', 
                           headers=[('X-Requested-With', 'XMLHttpRequest')], 
                           content_type='application/json', 
                           data=json.dumps(dict(ids=[node_id]))
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Section was deleted.")


    def test_synopsis(self):
        # Add a project so there is something to hang our node tests off.
        self.app.post('/add_project', data=dict(
            name='Synopsis Test Project',
            description='Automated Test Project for Checking Synopsis Behaviour',
            is_template=False,
            template=0
        ))
        
        # Add some text to the synopsis on the root node of our project.
        project = Project.query.filter(Project.name=='Synopsis Test Project').first()
        synopsis_id = project.structure[0].sectionsynopsis[0].id
        rv = self.app.post('/update_synopsis', 
                           data=dict(synopsis_id=synopsis_id, synopsis_text='Some text to show the update working.')
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Synopsis was updated.")
        self.assertEqual(data['status'], True)
        #Now try without any text - should fail.
        rv = self.app.post('/update_synopsis', 
                           data=dict(synopsis_id=synopsis_id)
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], 'Synopsis text is missing - no update was done.')
        self.assertEqual(data['status'], False)
        # And now with blank text - which is fine if a bit drastic.
        rv = self.app.post('/update_synopsis', 
                           data=dict(synopsis_id=synopsis_id, synopsis_text='')
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Synopsis was updated.")
        self.assertEqual(data['status'], True)
        

if __name__ == "__main__":
    unittest.main()