'''
Created on May 28, 2015

@author: sbrooks
'''
import unittest
import os
import auteur
import tempfile


class AuteurTestCase(unittest.TestCase):


    def setUp(self):
        self.db_fd, auteur.app.config['DATABASE'] = tempfile.mkstemp()
        auteur.app.config['TESTING'] = True
        self.app = auteur.app.test_client()
        auteur.database.init_db()


    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(auteur.app.config['DATABASE'])    


    def test_empty_db(self):
        rv = self.app.get('/')
        assert 'No entries here so far' in rv.data


    def test_project(self):
        rv = self.app.post('/add_project', data=dict(
            project_name=''
        ), follow_redirects=True)
        assert 'You need to name the project.' in rv.data
        
        rv = self.app.post('/add_project', data=dict(
            project_name='Automated Test Project'
        ), follow_redirects=True)
        assert 'You need to say something about the project.' in rv.data

        rv = self.app.post('/add_project', data=dict(
            project_description='Automated Test Project'
        ), follow_redirects=True)
        assert 'You need to name the project.' in rv.data
        
        rv = self.app.post('/add_project', data=dict(
            project_name='Automated Test Project',
            project_description='Automated Test Project Description goes here!'
        ), follow_redirects=True)
        assert 'Automated Test Project' in rv.data
        assert 'Automated Test Project Description goes here!' in rv.data
        
        rv = self.app.post('/add_project', data=dict(
            project_name='Automated Test Project',
            project_description='Automated Test Project Description goes here! Description is different.'
        ), follow_redirects=True)
        assert 'Name already used.  Maybe a writer should try to be more original?' in rv.data
    

if __name__ == "__main__":
    unittest.main()