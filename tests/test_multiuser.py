"""
Multi-user isolation tests for Auteur.

These tests check that one logged-in user can never read or write another
user's data: projects, structure nodes, section/synopsis/notes/characters
text, templates, exports and checkpoints.

They follow the same setUp/tearDown pattern as tests/tests.py, but use two
independent Flask test clients (each with its own cookie jar) so that
"Alice" and "Bob" can be logged in against the same app at the same time.

Run with:
    python -m unittest tests.test_multiuser -v
"""
import os
import unittest

from flask import json

from auteur import create_app
from auteur.models import Project, Structure, Checkpoint, db

from instance.config import basedir


class MultiUserTestCase(unittest.TestCase):

    def setUp(self):
        # See the note in tests/tests.py: the test DB URI MUST be passed via
        # test_config (create_app's argument), not set on app.config after
        # the fact, or db.create_all()/drop_all() will hit the real db.
        self.app_obj = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(basedir, 'test.db'),
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'BABEL_DEFAULT_LOCALE': 'en',
            'LANGUAGES': {'en': 'English'},
        })

        # IMPORTANT: do NOT keep an app_context pushed across test-client
        # requests. If one is already on top of the stack, Flask's request
        # dispatch reuses it instead of pushing a fresh one per request -
        # and Flask-Login caches the resolved user on flask.g the first
        # time it's read within a given app context. With a persistent
        # context, that cache is set once (by whichever login/register call
        # resolves last) and then silently reused for every later request
        # in the test, no matter which client/cookie made it - i.e. every
        # user looks like whoever logged in most recently. Only push a
        # context transiently, for direct ORM access between requests.
        with self.app_obj.app_context():
            db.create_all()

        # Two separate test_client() calls => two separate cookie jars =>
        # two independent, simultaneously logged-in sessions.
        self.alice = self.app_obj.test_client()
        self.bob = self.app_obj.test_client()

        self._register(self.alice, 'Alice', 'alice@example.com', 'alicepass123')
        self._register(self.bob, 'Bob', 'bob@example.com', 'bobpass123')

    def tearDown(self):
        with self.app_obj.app_context():
            db.session.remove()
            db.drop_all()

    def _query(self, fn):
        """Run fn() inside a short-lived app_context for direct ORM access
        between requests, without leaving a context pushed across
        requests (see the note in setUp)."""
        with self.app_obj.app_context():
            return fn()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _register(self, client, name, email, password):
        rv = client.post('/register', data=dict(
            name=name, email=email, password=password
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

    def _add_project(self, client, name, description='A description', is_template=False, template=0):
        # WTForms' BooleanField only treats '' or the literal string 'false'
        # as unchecked; posting Python False here would urlencode to the
        # string "False", which WTForms reads as *checked*. Mimic a real
        # HTML checkbox instead: omit the field entirely when unchecked.
        data = dict(name=name, description=description, template=template)
        if is_template:
            data['is_template'] = 'y'
        return client.post('/add_project', data=data, follow_redirects=True)

    def _project(self, name):
        return self._query(lambda: Project.query.filter(Project.name == name).first())

    def _structure_id(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].id
        return self._query(go)

    def _structure_title(self, structure_id):
        return self._query(lambda: Structure.query.get(structure_id).title)

    def _structure_exists(self, structure_id):
        return self._query(lambda: Structure.query.get(structure_id) is not None)

    def _child_count(self, parent_id):
        return self._query(lambda: Structure.query.filter_by(parent_id=parent_id).count())

    def _section_id(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].section.id
        return self._query(go)

    def _section_body(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].section.body
        return self._query(go)

    def _synopsis_id(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].sectionsynopsis.id
        return self._query(go)

    def _synopsis_body(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].sectionsynopsis.body
        return self._query(go)

    def _notes_id(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].sectionnotes.id
        return self._query(go)

    def _notes_body(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].sectionnotes.body
        return self._query(go)

    def _characters_id(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].sectioncharacters.id
        return self._query(go)

    def _characters_body(self, project_name):
        def go():
            project = Project.query.filter(Project.name == project_name).first()
            return project.structure[0].sectioncharacters.body
        return self._query(go)

    # ------------------------------------------------------------------
    # project list / template list scoping
    # ------------------------------------------------------------------
    def test_project_list_is_scoped_per_user(self):
        self._add_project(self.alice, 'Alice Project')
        self._add_project(self.bob, 'Bob Project')

        rv = self.alice.get('/get_project_list')
        self.assertIn(b'Alice Project', rv.data)
        self.assertNotIn(b'Bob Project', rv.data)

        rv = self.bob.get('/get_project_list')
        self.assertIn(b'Bob Project', rv.data)
        self.assertNotIn(b'Alice Project', rv.data)

    def test_template_list_is_scoped_per_user(self):
        self._add_project(self.alice, 'Alice Template', is_template=True)
        self._add_project(self.bob, 'Bob Template', is_template=True)

        rv = self.alice.get('/get_template_list')
        self.assertIn(b'Alice Template', rv.data)
        self.assertNotIn(b'Bob Template', rv.data)

        rv = self.bob.get('/get_template_list')
        self.assertIn(b'Bob Template', rv.data)
        self.assertNotIn(b'Alice Template', rv.data)

    def test_cannot_clone_another_users_template(self):
        # Alice makes a template with distinctive section content.
        self._add_project(self.alice, 'Alice Secret Template', is_template=True)
        template = self._project('Alice Secret Template')
        section_id = self._section_id('Alice Secret Template')
        self.alice.post('/update_section', data=dict(
            section_id=section_id, section_text='Alice secret template text.'
        ))

        # Bob tries to create a project using Alice's template id directly
        # (bypassing the <select> he would normally see, which only lists
        # his own templates). ProjectForm.template is a SelectField whose
        # choices are built per-request from the current user's templates,
        # so WTForms should reject a value that isn't one of Bob's own
        # choices, and no project should be created from it.
        rv = self._add_project(self.bob, 'Bobs Cloned Project', template=template.id)
        self.assertEqual(rv.status_code, 200)
        self.assertIsNone(self._project('Bobs Cloned Project'))

    # ------------------------------------------------------------------
    # project-level ownership
    # ------------------------------------------------------------------
    def test_cannot_view_another_users_project(self):
        self._add_project(self.alice, 'Alice Private Project')
        project = self._project('Alice Private Project')

        rv = self.bob.get('/project/%d/' % project.id)
        self.assertEqual(rv.status_code, 404)

        # Alice herself can still view it.
        rv = self.alice.get('/project/%d/' % project.id)
        self.assertEqual(rv.status_code, 200)

    def test_cannot_update_another_users_project(self):
        self._add_project(self.alice, 'Alice Project To Protect')
        project = self._project('Alice Project To Protect')

        rv = self.bob.post('/update_project/%d' % project.id, data=dict(
            name='Hijacked Name',
            description='Hijacked description',
            is_template=False,
        ))
        self.assertEqual(rv.status_code, 404)

        self.assertIsNotNone(self._project('Alice Project To Protect'))
        self.assertIsNone(self._project('Hijacked Name'))

    def test_cannot_delete_or_undelete_another_users_project(self):
        self._add_project(self.alice, 'Alice Project To Keep')
        project = self._project('Alice Project To Keep')

        rv = self.bob.post('/delete_project/%d' % project.id)
        self.assertEqual(rv.status_code, 404)
        self.assertFalse(self._project('Alice Project To Keep').is_deleted)

        # Alice deletes her own project, then Bob tries to undelete it.
        self.alice.post('/delete_project/%d' % project.id)
        self.assertTrue(self._project('Alice Project To Keep').is_deleted)

        rv = self.bob.post('/undelete_project/%d' % project.id)
        self.assertEqual(rv.status_code, 404)
        project = self._project('Alice Project To Keep')
        self.assertTrue(project.is_deleted)

    def test_cannot_get_another_users_project_tree(self):
        self._add_project(self.alice, 'Alice Tree Project')
        project = self._project('Alice Tree Project')

        rv = self.bob.get('/get_project_tree?project_id=%d' % project.id)
        self.assertEqual(rv.status_code, 404)

    def test_cannot_export_another_users_project(self):
        self._add_project(self.alice, 'Alice Export Project')
        project = self._project('Alice Export Project')

        rv = self.bob.get('/export_project/%d' % project.id)
        self.assertEqual(rv.status_code, 404)

    # ------------------------------------------------------------------
    # structure-node ownership (add/rename/delete nodes)
    # ------------------------------------------------------------------
    def test_cannot_get_section_of_another_users_structure(self):
        self._add_project(self.alice, 'Alice Structure Project')
        structure_id = self._structure_id('Alice Structure Project')

        rv = self.bob.get('/get_section?structure_id=%d' % structure_id)
        self.assertEqual(rv.status_code, 404)

    def test_cannot_rename_another_users_node(self):
        self._add_project(self.alice, 'Alice Rename Project')
        structure_id = self._structure_id('Alice Rename Project')
        original_title = self._structure_title(structure_id)

        rv = self.bob.post('/update_node',
                           headers=[('X-Requested-With', 'XMLHttpRequest')],
                           content_type='application/json',
                           data=json.dumps(dict(id=structure_id, text='Hijacked Title')))
        self.assertEqual(rv.status_code, 404)

        self.assertEqual(self._structure_title(structure_id), original_title)

    def test_cannot_delete_another_users_node(self):
        self._add_project(self.alice, 'Alice Delete Node Project')
        structure_id = self._structure_id('Alice Delete Node Project')

        rv = self.bob.post('/delete_node',
                           headers=[('X-Requested-With', 'XMLHttpRequest')],
                           content_type='application/json',
                           data=json.dumps(dict(id=structure_id)))
        self.assertEqual(rv.status_code, 404)

        # The node should still be there.
        self.assertTrue(self._structure_exists(structure_id))

    def test_cannot_add_node_to_another_users_project(self):
        self._add_project(self.alice, 'Alice Add Node Project')
        root_id = self._structure_id('Alice Add Node Project')
        children_before = self._child_count(root_id)

        # add_node currently has no ownership check on project_id/parent at
        # all (unlike most of the other editor.py routes) - it will happily
        # attach a new node under another user's tree. This test documents
        # that gap; see the note in the accompanying summary.
        project = self._project('Alice Add Node Project')
        rv = self.bob.post('/add_node/%d' % project.id,
                           headers=[('X-Requested-With', 'XMLHttpRequest')],
                           content_type='application/json',
                           data=json.dumps(dict(pos='last', parent=root_id)))

        children_after = self._child_count(root_id)
        self.assertEqual(
            children_before, children_after,
            "Bob was able to add a node to Alice's project - add_node() is "
            "missing an ownership check on project_id/parent."
        )

    # ------------------------------------------------------------------
    # section / synopsis / notes / characters ownership
    # ------------------------------------------------------------------
    def test_cannot_update_another_users_section_text(self):
        self._add_project(self.alice, 'Alice Section Project')
        section_id = self._section_id('Alice Section Project')

        rv = self.bob.post('/update_section', data=dict(
            section_id=section_id, section_text='Hijacked section text.'
        ))
        self.assertEqual(rv.status_code, 404)

        self.assertEqual(self._section_body('Alice Section Project'), '')

    def test_cannot_update_another_users_synopsis(self):
        self._add_project(self.alice, 'Alice Synopsis Project')
        synopsis_id = self._synopsis_id('Alice Synopsis Project')

        rv = self.bob.post('/update_synopsis', data=dict(
            synopsis_id=synopsis_id, synopsis_text='Hijacked synopsis.'
        ))
        self.assertEqual(rv.status_code, 404)

        self.assertEqual(self._synopsis_body('Alice Synopsis Project'), '')

    def test_cannot_update_another_users_notes(self):
        self._add_project(self.alice, 'Alice Notes Project')
        notes_id = self._notes_id('Alice Notes Project')

        rv = self.bob.post('/update_notes', data=dict(
            notes_id=notes_id, notes_text='Hijacked notes.'
        ))
        self.assertEqual(rv.status_code, 404)

        self.assertEqual(self._notes_body('Alice Notes Project'), '')

    def test_cannot_update_another_users_characters(self):
        self._add_project(self.alice, 'Alice Characters Project')
        characters_id = self._characters_id('Alice Characters Project')

        rv = self.bob.post('/update_characters', data=dict(
            character_id=characters_id, character_text='Hijacked characters.'
        ))
        self.assertEqual(rv.status_code, 404)

        self.assertEqual(self._characters_body('Alice Characters Project'), '')

    # ------------------------------------------------------------------
    # checkpoints
    #
    # NOTE: create_checkpoint() and restore_checkpoint() in editor.py do
    # not currently call get_owned_project_or_404() (or equivalent) at
    # all, unlike every other route in the blueprint. These two tests are
    # written to describe the *intended* multi-user behaviour and will
    # fail against the current code - that failure is a real finding, not
    # a broken test, and is worth fixing:
    #   - create_checkpoint(project_id) should 404 if project_id isn't
    #     owned by current_user.
    #   - restore_checkpoint(checkpoint_id) should 404 if the checkpoint's
    #     project isn't owned by current_user.
    # ------------------------------------------------------------------
    def test_cannot_create_checkpoint_for_another_users_project(self):
        self._add_project(self.alice, 'Alice Checkpoint Project')
        project = self._project('Alice Checkpoint Project')

        rv = self.bob.post('/create_checkpoint/%d' % project.id, data=dict(label='Bobs Checkpoint'))
        self.assertEqual(
            rv.status_code, 404,
            "Bob was able to create a checkpoint on Alice's project - "
            "create_checkpoint() is missing an ownership check on project_id."
        )

    def test_cannot_restore_checkpoint_of_another_users_project(self):
        self._add_project(self.alice, 'Alice Restore Project')
        project = self._project('Alice Restore Project')
        section_id = self._section_id('Alice Restore Project')

        self.alice.post('/update_section', data=dict(
            section_id=section_id, section_text='Original text.'
        ))
        rv = self.alice.post('/create_checkpoint/%d' % project.id, data=dict(label='Before edits'))
        checkpoint_id = json.loads(rv.data)['checkpoint_id']

        self.alice.post('/update_section', data=dict(
            section_id=section_id, section_text='Edited text.'
        ))

        rv = self.bob.post('/restore_checkpoint/%d' % checkpoint_id)
        self.assertEqual(
            rv.status_code, 404,
            "Bob was able to restore a checkpoint belonging to Alice's "
            "project - restore_checkpoint() is missing an ownership check."
        )

        self.assertEqual(self._section_body('Alice Restore Project'), 'Edited text.')


if __name__ == '__main__':
    unittest.main()