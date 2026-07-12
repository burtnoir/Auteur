"""
Sets up some test data.
"""
from auteur import create_app
from auteur.models import db, Project, Structure, Section, SectionSynopsis, SectionNotes, SectionCharacters

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create the first project
    project = Project(name='First Test Project', description='A description is required for the first project', is_template=False, is_deleted=False)
    db.session.add(project)

    root_structure = Structure(title="First project structure leaf.", displayorder=1, project=project)
    db.session.add(root_structure)

    db.session.add(Section(body="First project and structure leaf body text.", structure=root_structure))
    db.session.add(SectionSynopsis(body="", structure=root_structure))
    db.session.add(SectionNotes(body="First project and leaf notes text.", structure=root_structure))
    db.session.add(SectionCharacters(body="", structure=root_structure))

    structure = Structure(title="Second leaf.", project=project, displayorder=2, parent=root_structure)
    db.session.add(structure)

    db.session.add(Section(body="Second leaf body text.", structure=structure))
    db.session.add(SectionSynopsis(body="Second leaf synopsis text.", structure=structure))
    db.session.add(SectionNotes(body="", structure=structure))
    db.session.add(SectionCharacters(body="Second leaf characters text.", structure=structure))

    structure = Structure(title="Third leaf.", project=project, displayorder=3, parent=root_structure)
    db.session.add(structure)

    db.session.add(Section(body="Third leaf body text.", structure=structure))
    db.session.add(SectionSynopsis(body="Third leaf synopsis text.", structure=structure))
    db.session.add(SectionNotes(body="", structure=structure))
    db.session.add(SectionCharacters(body="Third leaf characters text.", structure=structure))

    db.session.commit()

    # Create the second project
    project = Project(name='Second Project', description='A description is required for the first project', is_template=False, is_deleted=False)
    db.session.add(project)

    root_structure = Structure(title="Second project structure leaf.", displayorder=1, project=project)
    db.session.add(root_structure)

    db.session.add(Section(body="Second project and structure leaf body text.", structure=root_structure))
    db.session.add(SectionSynopsis(body="Second project synopsis text.", structure=root_structure))
    db.session.add(SectionNotes(body="", structure=root_structure))
    db.session.add(SectionCharacters(body="", structure=root_structure))

    structure = Structure(title="Second leaf.", project=project, displayorder=2, parent=root_structure)
    db.session.add(structure)

    db.session.add(Section(body="Second leaf body text.", structure=structure))
    db.session.add(SectionSynopsis(body="Second leaf and second project synopsis text.", structure=structure))
    db.session.add(SectionNotes(body="", structure=structure))
    db.session.add(SectionCharacters(body="", structure=structure))

    structure = Structure(title="Third leaf.", project=project, displayorder=3, parent=root_structure)
    db.session.add(structure)

    db.session.add(Section(body="Third leaf body text.", structure=structure))
    db.session.add(SectionSynopsis(body="Second leaf synopsis text.", structure=structure))
    db.session.add(SectionNotes(body="And some notes go here.", structure=structure))
    db.session.add(SectionCharacters(body="", structure=structure))

    db.session.commit()

    # Create a template - which is really a project
    project = Project(name='Template', description='A description for the template.', is_template=True, is_deleted=False)
    db.session.add(project)

    root_structure = Structure(title="Template leaf.", displayorder=1, project=project)
    db.session.add(root_structure)

    db.session.add(Section(body="Template leaf body text.", structure=root_structure))
    db.session.add(SectionSynopsis(body="", structure=root_structure))
    db.session.add(SectionNotes(body="", structure=root_structure))
    db.session.add(SectionCharacters(body="", structure=root_structure))

    db.session.commit()

    # Create the third (deleted) project
    project = Project(name='Project that has been deleted.', description='This project was deleted - but don''t worry because it''s only a logical Delete.', is_template=False, is_deleted=True)
    db.session.add(project)

    root_structure = Structure(title="Deleted project structure leaf.", displayorder=1, project=project)
    db.session.add(root_structure)

    db.session.add(Section(body="deleted project and structure leaf body text.", structure=root_structure))
    db.session.add(SectionSynopsis(body="Deleted project synopsis text.", structure=root_structure))
    db.session.add(SectionNotes(body="", structure=root_structure))
    db.session.add(SectionCharacters(body="", structure=root_structure))

    structure = Structure(title="Second leaf.", project=project, displayorder=2, parent=root_structure)
    db.session.add(structure)

    db.session.add(Section(body="Second leaf body text.", structure=structure))
    db.session.add(SectionSynopsis(body="Second leaf on deleted project synopsis text.", structure=structure))
    db.session.add(SectionNotes(body="", structure=structure))
    db.session.add(SectionCharacters(body="", structure=structure))

    structure = Structure(title="Third leaf.", project=project, displayorder=3, parent=root_structure)
    db.session.add(structure)

    db.session.add(Section(body="Third leaf body text.", structure=structure))
    db.session.add(SectionSynopsis(body="Second leaf synopsis text.", structure=structure))
    db.session.add(SectionNotes(body="And some notes go here.", structure=structure))
    db.session.add(SectionCharacters(body="", structure=structure))

    db.session.commit()

    # Create a deleted template - which is really a project
    project = Project(name='Deleted Template', description='A description for the deleted template.', is_template=True, is_deleted=True)
    db.session.add(project)

    root_structure = Structure(title="Template leaf.", displayorder=1, project=project)
    db.session.add(root_structure)

    db.session.add(Section(body="Template leaf body text.  My project has been deleted.", structure=root_structure))
    db.session.add(SectionSynopsis(body="", structure=root_structure))
    db.session.add(SectionNotes(body="", structure=root_structure))
    db.session.add(SectionCharacters(body="", structure=root_structure))

    db.session.commit()
