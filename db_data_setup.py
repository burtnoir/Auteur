'''
Sets up some test data.
'''
from auteur.database import db_session
from auteur.database import init_db, drop_db
from auteur.models import Project, Structure, Section, SectionSynopsis, \
    SectionNotes


drop_db()
init_db()

# Create the first project
project = Project(name='First Test Project', description='A description is required for the first project', is_template=False)
db_session.add(project)

root_structure = Structure(title="First project structure leaf.", displayorder=1, project=project)
db_session.add(root_structure)

db_session.add(Section(body="First project and structure leaf body text.", structure=root_structure))
db_session.add(SectionSynopsis(body="", structure=root_structure))
db_session.add(SectionNotes(body="First project and leaf notes text.", structure=root_structure))

structure = Structure(title="Second leaf.", project=project, displayorder=2, parent=root_structure)
db_session.add(structure)

db_session.add(Section(body="Second leaf body text.", structure=structure))
db_session.add(SectionSynopsis(body="Second leaf synopsis text.", structure=structure))
db_session.add(SectionNotes(body="", structure=structure))

structure = Structure(title="Third leaf.", project=project, displayorder=3, parent=root_structure)
db_session.add(structure)

db_session.add(Section(body="Third leaf body text.", structure=structure))
db_session.add(SectionSynopsis(body="Third leaf synopsis text.", structure=structure))
db_session.add(SectionNotes(body="", structure=structure))

db_session.commit()


# Create the second project
project = Project(name='Second Project', description='A description is required for the first project', is_template=False)
db_session.add(project)

root_structure = Structure(title="Second project structure leaf.", displayorder=1, project=project)
db_session.add(root_structure)

db_session.add(Section(body="Second project and structure leaf body text.", structure=root_structure))
db_session.add(SectionSynopsis(body="Second project synopsis text.", structure=root_structure))
db_session.add(SectionNotes(body="", structure=root_structure))


structure = Structure(title="Second leaf.", project=project, displayorder=2, parent=root_structure)
db_session.add(structure)

db_session.add(Section(body="Second leaf body text.", structure=structure))
db_session.add(SectionSynopsis(body="Second leaf and second project synopsis text.", structure=structure))
db_session.add(SectionNotes(body="", structure=structure))


structure = Structure(title="Third leaf.", project=project, displayorder=3, parent=root_structure)
db_session.add(structure)

db_session.add(Section(body="Third leaf body text.", structure=structure))
db_session.add(SectionSynopsis(body="Second leaf synopsis text.", structure=structure))
db_session.add(SectionNotes(body="And some notes go here.", structure=structure))

db_session.commit()


# Create a template - which is really a project
project = Project(name='Template', description='A description for the template.', is_template=True)
db_session.add(project)

root_structure = Structure(title="Template leaf.", displayorder=1, project=project)
db_session.add(root_structure)

db_session.add(Section(body="Template leaf body text.", structure=root_structure))
db_session.add(SectionSynopsis(body="", structure=root_structure))
db_session.add(SectionNotes(body="", structure=root_structure))

db_session.commit()