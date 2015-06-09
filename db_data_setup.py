from auteur.database import init_db, drop_db
from auteur.database import db_session
from auteur.models import Project, Structure, Section


'''
Sets up some test data so I can see things working while I don't have the ability
to add it through the front end.
'''
drop_db()
init_db()

# Create the first project
project = Project(name='First Test Project', description='A description is required for the first project')
db_session.add(project)
db_session.commit()

root_structure = Structure(title="First project structure leaf.", displayorder=1, project=project)
db_session.add(root_structure)
db_session.commit()

section = Section(body="First project and structure leaf body text.", structure=root_structure)
db_session.add(section)
db_session.commit()

structure = Structure(title="Second leaf.", project=project, displayorder=2, parent=root_structure)
db_session.add(structure)
db_session.commit()

section = Section(body="Second leaf body text.", structure=structure)
db_session.add(section)
db_session.commit()

structure = Structure(title="Third leaf.", project=project, displayorder=3, parent=root_structure)
db_session.add(structure)
db_session.commit()

section = Section(body="Third leaf body text.", structure=structure)
db_session.add(section)
db_session.commit()

# Create the second project
project = Project(name='Second Project', description='A description is required for the first project')
db_session.add(project)
db_session.commit()

root_structure = Structure(title="Second project structure leaf.", displayorder=1, project=project)
db_session.add(root_structure)
db_session.commit()

section = Section(body="Second project and structure leaf body text.", structure=root_structure)
db_session.add(section)
db_session.commit()

structure = Structure(title="Second leaf.", project=project, displayorder=2, parent=root_structure)
db_session.add(structure)
db_session.commit()

section = Section(body="Second leaf body text.", structure=structure)
db_session.add(section)
db_session.commit()

structure = Structure(title="Third leaf.", project=project, displayorder=3, parent=root_structure)
db_session.add(structure)
db_session.commit()

section = Section(body="Third leaf body text.", structure=structure)
db_session.add(section)
db_session.commit()