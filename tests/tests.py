"""
Created on May 28, 2015

@author: sbrooks
"""
import os
import unittest
from auteur import create_app
from auteur.models import Project, Section, db
from flask import json

from instance.config import basedir


class ProjectTestCase(unittest.TestCase):

    def setUp(self):
        # NOTE: the test database URI (and any other config the app needs at
        # init time) MUST be supplied via the `test_config` argument of
        # create_app(), not set on app.config afterwards. Flask-SQLAlchemy
        # binds its engine to whatever SQLALCHEMY_DATABASE_URI is configured
        # at the moment db.init_app() runs (i.e. inside create_app()) and
        # ignores any later changes to app.config. Overriding it afterwards
        # (as this used to do) silently left the engine pointed at the real
        # instance/auteur.db, so db.create_all()/db.drop_all() below were
        # actually wiping out the production database instead of test.db.
        self.app_obj = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(basedir, 'test.db'),
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'BABEL_DEFAULT_LOCALE': 'en',
            'LANGUAGES': {'en': 'English'},
        })
        self.app = self.app_obj.test_client()
        self.ctx = self.app_obj.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_empty_db(self):
        rv = self.app.get('/')
        self.assertIn(b'No entries here so far', rv.data)

    def test_project(self):
        rv = self.app.post('/add_project', data=dict(
            name=''
        ), follow_redirects=True)
        self.assertIn(b'You need to name the project.', rv.data)

        rv = self.app.post('/add_project', data=dict(
            name='Automated Test Project'
        ), follow_redirects=True)
        self.assertIn(b'You need to say something about the project.', rv.data)

        rv = self.app.post('/add_project', data=dict(
            name='',
            description='Automated Test Project'
        ), follow_redirects=True)
        self.assertIn(b'You need to name the project.', rv.data)

        # Expected to work and set up the situation for the duplication test.
        rv = self.app.post('/add_project', data=dict(
            name='Automated Test Project',
            description='Automated Test Project Description goes here!',
            is_template=False,
            template=0
        ), follow_redirects=True)
        self.assertIn(b'Automated Test Project', rv.data)
        self.assertIn(b'Automated Test Project Description goes here!', rv.data)

        # Check we can't use the same name twice.
        rv = self.app.post('/add_project', data=dict(
            name='Automated Test Project',
            description='Automated Test Project Description goes here! Description is different.',
            is_template=False,
            template=0
        ), follow_redirects=True)
        self.assertIn(b'Name already used.  Maybe a writer should try to be more original?', rv.data)

        # Get the project id so we can try some updates.
        project_id = Project.query.with_entities(Project.id).filter(Project.name == 'Automated Test Project').first()[0]

        with self.app as c:
            with c.session_transaction() as sess:
                sess['project_id'] = project_id

            # Check we can update the description.
            rv = c.post('/update_project/' + str(project_id),
                        data=dict(
                            name='Automated Test Project',
                            description='The description has been updated.',
                            is_template=False,
                            template=0
                        ))
            data = json.loads(rv.data)
            if not data.get('status'):
                print(f"Update failed with errors: {data}")
            self.assertEqual(data.get('status_text'), "Hoorah! Project details were updated.")

            # Check we can update the name.
            rv = c.post('/update_project/' + str(project_id),
                        data=dict(
                            name='The Name Updated',
                            description='The description has been updated.',
                            is_template=False,
                            template=0
                        ))
            data = json.loads(rv.data)
            self.assertEqual(data['status_text'], "Hoorah! Project details were updated.")

    def test_nodes(self):
        # Add a project so there is something to hang our node tests off.
        self.app.post('/add_project', data=dict(
            name='Node Test Project',
            description='Automated Test Project for Checking Node Behaviour',
            is_template=False,
            template=0
        ))

        # Add a new node to the root node of our project.
        project_id = Project.query.with_entities(Project.id).filter(Project.name == 'Node Test Project').first()
        rv = self.app.post('/add_node/' + str(project_id.id),
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
        project = Project.query.filter(Project.name == 'Synopsis Test Project').first()
        synopsis_id = project.structure[0].sectionsynopsis.id
        rv = self.app.post('/update_synopsis',
                           data=dict(synopsis_id=synopsis_id, synopsis_text='Some text to show the update working.')
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Synopsis was updated.")
        self.assertEqual(data['status'], True)
        # Now try without any text - should fail.
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

    def test_notes(self):
        # Add a project so there is something to hang our node tests off.
        self.app.post('/add_project', data=dict(
            name='Notes Test Project',
            description='Automated Test Project for Checking Notes Behaviour',
            is_template=False,
            template=0
        ))

        # Add some text to the notes on the root node of our project.
        project = Project.query.filter(Project.name == 'Notes Test Project').first()
        notes_id = project.structure[0].sectionnotes.id
        rv = self.app.post('/update_notes',
                           data=dict(notes_id=notes_id, notes_text='Some text to show the update working.')
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Notes was updated.")
        self.assertEqual(data['status'], True)
        # Now try without any text - should fail.
        rv = self.app.post('/update_notes',
                           data=dict(notes_id=notes_id)
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], 'Notes text is missing - no update was done.')
        self.assertEqual(data['status'], False)
        # And now with blank text - which is fine if a bit drastic.
        rv = self.app.post('/update_notes',
                           data=dict(notes_id=notes_id, notes_text='')
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Notes was updated.")
        self.assertEqual(data['status'], True)

    def test_characters(self):
        # Add a project so there is something to hang our node tests off.
        self.app.post('/add_project', data=dict(
            name='Characters Test Project',
            description='Automated Test Project for Checking Characters Behaviour',
            is_template=False,
            template=0
        ))

        # Add a second node so we can prove each node's characters are independent.
        project = Project.query.filter(Project.name == 'Characters Test Project').first()
        root_structure = project.structure[0]
        rv = self.app.post('/add_node/' + str(project.id),
                           headers=[('X-Requested-With', 'XMLHttpRequest')],
                           content_type='application/json',
                           data=json.dumps(dict(pos='last', parent=root_structure.id))
                           )
        second_node_id = json.loads(rv.data)['id']

        # Add some text to the characters on the root node of our project.
        characters_id = root_structure.sectioncharacters.id
        rv = self.app.post('/update_characters',
                           data=dict(character_id=characters_id, character_text='Some text to show the update working.')
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Characters was updated.")
        self.assertEqual(data['status'], True)
        # Now try without any text - should fail.
        rv = self.app.post('/update_characters',
                           data=dict(character_id=characters_id)
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], 'Characters text is missing - no update was done.')
        self.assertEqual(data['status'], False)
        # And now with blank text - which is fine if a bit drastic.
        rv = self.app.post('/update_characters',
                           data=dict(character_id=characters_id, character_text='')
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Characters was updated.")
        self.assertEqual(data['status'], True)

        # Now make sure the second node has its own, independent characters text - it
        # should not have picked up the text saved against the first (root) node.
        rv = self.app.get('/get_section?' + 'structure_id=' + str(second_node_id))
        data = json.loads(rv.data)
        self.assertEqual(data['characters_text'], '')
        self.assertNotEqual(data['characters_id'], characters_id)

    def test_update_section(self):
        # Add a project so there is something to hang our node tests off.
        self.app.post('/add_project', data=dict(
            name='Update Section Test Project',
            description='Automated Test Project for Checking Section Update Behaviour',
            template=0
        ))

        project = Project.query.filter(Project.name == 'Update Section Test Project').first()
        section_id = project.structure[0].section.id

        rv = self.app.post('/update_section',
                           data=dict(section_id=section_id, sectiontext='Some new section text.')
                           )
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Section save was a Complete Success!")
        self.assertEqual(data['status'], True)

        section = Section.query.filter(Section.id == section_id).first()
        self.assertEqual(section.body, 'Some new section text.')

    def test_delete_and_undelete_project(self):
        # Add a project we can delete and then undelete.
        self.app.post('/add_project', data=dict(
            name='Delete Test Project',
            description='Automated Test Project for Checking Delete/Undelete Behaviour',
            template=0
        ))
        project = Project.query.filter(Project.name == 'Delete Test Project').first()
        self.assertFalse(project.is_deleted)

        # Deleted projects should no longer show in the main project list ...
        rv = self.app.post('/delete_project/' + str(project.id), follow_redirects=True)
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Project was deleted.")
        self.assertEqual(data['status'], True)

        db.session.refresh(project)
        self.assertTrue(project.is_deleted)

        rv = self.app.get('/get_project_list')
        self.assertNotIn(b'Delete Test Project', rv.data)

        # ... but should show up in the deleted projects list.
        rv = self.app.get('/get_deleted_project_list')
        self.assertIn(b'Delete Test Project', rv.data)

        # Undeleting should reverse the above.
        rv = self.app.post('/undelete_project/' + str(project.id), follow_redirects=True)
        data = json.loads(rv.data)
        self.assertEqual(data['status_text'], "Hoorah! Project was undeleted.")
        self.assertEqual(data['status'], True)

        db.session.refresh(project)
        self.assertFalse(project.is_deleted)

        rv = self.app.get('/get_project_list')
        self.assertIn(b'Delete Test Project', rv.data)

        rv = self.app.get('/get_deleted_project_list')
        self.assertNotIn(b'Delete Test Project', rv.data)

    def test_templates_and_cloning(self):
        # Create a project and mark it as a template.
        self.app.post('/add_project', data=dict(
            name='Template Source Project',
            description='Automated Test Project used as a Template',
            is_template=True,
            template=0
        ))
        template_project = Project.query.filter(Project.name == 'Template Source Project').first()
        self.assertTrue(template_project.is_template)

        # It should show up in the template list.
        rv = self.app.get('/get_template_list')
        self.assertIn(b'Template Source Project', rv.data)

        # Give the template's root section some distinctive content to check it gets copied.
        root_structure = template_project.structure[0]
        self.app.post('/update_section',
                      data=dict(section_id=root_structure.section.id, sectiontext='Template section text.')
                      )

        # Now create a new project based on that template.
        self.app.post('/add_project', data=dict(
            name='Cloned Project',
            description='Automated Test Project cloned from a Template',
            template=template_project.id
        ))
        cloned_project = Project.query.filter(Project.name == 'Cloned Project').first()
        self.assertIsNotNone(cloned_project)
        self.assertFalse(cloned_project.is_template)

        cloned_structure = cloned_project.structure[0]
        # The cloned node should have its own copy of the content, not a shared reference.
        self.assertEqual(cloned_structure.section.body, 'Template section text.')
        self.assertNotEqual(cloned_structure.section.id, root_structure.section.id)

        # A deleted template should show up in the deleted templates list, not the active one.
        rv = self.app.post('/delete_project/' + str(template_project.id))
        self.assertEqual(json.loads(rv.data)['status'], True)

        rv = self.app.get('/get_template_list')
        self.assertNotIn(b'Template Source Project', rv.data)
        rv = self.app.get('/get_deleted_template_list')
        self.assertIn(b'Template Source Project', rv.data)

    def test_export_project(self):
        # Add a project with some section content to export.
        self.app.post('/add_project', data=dict(
            name='Export Test Project',
            description='Automated Test Project for Checking Export Behaviour',
            template=0
        ))
        project = Project.query.filter(Project.name == 'Export Test Project').first()
        section = project.structure[0].section
        section.body = 'Exported section content.'
        db.session.commit()

        rv = self.app.get('/export_project/' + str(project.id))
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Exported section content.', rv.data)
        self.assertIn('Export Test Project.html', rv.headers.get('Content-Disposition', ''))

    def test_show_content(self):
        # Add a project so there is something to render.
        self.app.post('/add_project', data=dict(
            name='Show Content Test Project',
            description='Automated Test Project for Checking Content Rendering',
            template=0
        ))
        project = Project.query.filter(Project.name == 'Show Content Test Project').first()
        structure_id = project.structure[0].id

        # Without a structure id the first structure item should be shown.
        rv = self.app.get('/project/' + str(project.id) + '/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Show Content Test Project', rv.data)

        # With an explicit structure id the same content should be shown.
        rv = self.app.get('/project/' + str(project.id) + '/' + str(structure_id))
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Show Content Test Project', rv.data)

    def test_project_short_description(self):
        short_project = Project(name='Short', description='A short description.')
        self.assertEqual(short_project.short_description, 'A short description.')

        long_description = 'x' * 200
        long_project = Project(name='Long', description=long_description)
        self.assertEqual(long_project.short_description, ('x' * 150) + '...')

    def test_project_name_length_validation(self):
        rv = self.app.post('/add_project', data=dict(
            name='y' * 257,
            description='Automated Test Project for Checking Name Length Validation'
        ), follow_redirects=True)
        self.assertIn(b'This name is too long - 256 characters should be enough for anyone.', rv.data)


if __name__ == "__main__":
    unittest.main()
