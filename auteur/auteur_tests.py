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
        assert 'Unbelievable.  No entries here so far' in rv.data


    def testName(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()