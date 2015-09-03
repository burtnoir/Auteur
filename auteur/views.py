'''
Created on Apr 25, 2015

@author: sbrooks
'''
from flask import stream_with_context, Response
from flask.globals import request
from flask.helpers import url_for, flash
from flask.json import jsonify
from flask.templating import render_template
from sqlalchemy.sql.functions import func
from werkzeug.datastructures import Headers
from werkzeug.utils import redirect

from auteur import app
from auteur.database import db_session
from auteur.forms import ProjectForm
from auteur.models import Project, Structure, Section, SectionSynopsis, \
    SectionNotes
from auteur import babel
import auteur
from flask_babel import gettext

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(auteur.app.config['LANGUAGES'].keys())

@app.route('/')
@app.route('/get_project_list', methods=['GET'])
def get_project_list():

    projects = Project.query.filter(Project.is_deleted==False).filter(Project.is_template==False).all()
    return get_project_list_helper(projects)


@app.route('/get_template_list', methods=['GET'])
def get_template_list():

    projects = Project.query.filter(Project.is_deleted==False).filter(Project.is_template).all()
    return get_project_list_helper(projects)


@app.route('/get_deleted_template_list', methods=['GET'])
def get_deleted_template_list():

    projects = Project.query.filter(Project.is_deleted).filter(Project.is_template).all()
    return get_project_list_helper(projects)


@app.route('/get_deleted_project_list', methods=['GET'])
def get_deleted_project_list():
    '''
    Get a list of deleted projects for display.
    '''
    projects = Project.query.filter(Project.is_deleted).filter(Project.is_template==False).all()
    return get_project_list_helper(projects)


def get_project_list_helper(projects):
    form = ProjectForm(request.form)
    form.template.choices = [(t.id, t.name) for t in Project.query.order_by('name').filter(Project.is_template).filter(Project.is_deleted==False)]
    form.template.choices.insert(0, (0, gettext('-- Choose a Template --')))
    return render_template('index.html', 
                           projects=projects, 
                           form=form)


@app.route('/project/<int:project_id>/', defaults={'structure_id' : None})
@app.route('/project/<int:project_id>/<int:structure_id>')
def show_content(project_id, structure_id):
    # show the project with the given id, the id is an integer
    project = Project.query.filter_by(id=project_id).first()
    form = ProjectForm(obj=project)
    del form.template
    structure = Structure.query.filter_by(project_id=project.id)
    
    # If the id wasn't passed (probably because the call is from the project page)
    # then open the first structure item's text.
    if structure_id is None:
        structure_id = structure[0].id
    section = Section.query.filter_by(structure_id=structure_id).first()
    synopsis = SectionSynopsis.query.filter_by(structure_id=structure_id).first()
    notes = SectionNotes.query.filter_by(structure_id=structure_id).first()
    return render_template('content.html', 
                           project=project, 
                           structure=structure, 
                           section=section, 
                           synopsis=synopsis, 
                           notes=notes, 
                           form=form)


@app.route('/get_section', methods=['GET'])
def get_section():
    '''
    Get the contents of a section for display.
    '''
    structure_id = request.args.get('structure_id', 0, type=int)
    section = Section.query.filter_by(structure_id=structure_id).first()
    synopsis = SectionSynopsis.query.filter_by(structure_id=structure_id).first()
    notes = SectionNotes.query.filter_by(structure_id=structure_id).first()
    return jsonify(section_text=section.body, 
                   section_id=section.id, 
                   synopsis_text=synopsis.body, 
                   synopsis_id=synopsis.id, 
                   notes_text=notes.body, 
                   notes_id=notes.id)


@app.route('/add_project', methods=['POST'])
def add_project():
    '''
    Add a project.  Default a tree structure and sections to go with them.
    '''
    form = ProjectForm(request.form)
    form.template.choices = [(t.id, t.name) for t in Project.query.order_by('name').filter(Project.is_template)]
    form.template.choices.insert(0, (0, gettext('-- Choose a Template --')))
    if form.validate():
        project = Project(name=form.name.data, description=form.description.data, is_template=form.is_template.data)
        db_session.add(project)

        if form.template.data != 0:
            copy_from_template(project, form.template.data)
        else:
            create_node(project=project, title=form.name.data)
        
        db_session.commit()
    
        flash('New Project Added')
        return redirect(url_for('show_content', project_id=project.id, structure_id=None))
    
    projects = Project.query.all()
    return render_template('index.html', 
                           projects=projects, 
                           form=form)


def copy_from_template(project, template_id):
    '''
    Get the template contents and add them to the new project.
    '''
    structure_map = {}
    for structure, section, synopsis, notes in \
            db_session.query(Structure, Section, SectionSynopsis, SectionNotes).\
            filter(Structure.id == Section.structure_id).\
            filter(Structure.id == SectionSynopsis.structure_id).\
            filter(Structure.id == SectionNotes.structure_id).\
            filter(Structure.project_id == template_id).order_by(Structure.parent_id).all():
        
        # Check the map to find the new parent.
        new_parent = None
        if structure.parent and structure.parent_id in structure_map:
            new_parent = structure_map[structure.parent_id]
        # Create the new structure element using the discovered parent.  If nothing was found
        # then it has no parent and so is a root element.
        new_structure = Structure(parent=new_parent, title=structure.title, displayorder=structure.displayorder, project=project)
        db_session.add(new_structure)
        # Every time a structure record is processed we add it to the map to link the 
        # template element to the newly created element.
        structure_map[structure.id] = new_structure
        db_session.add(Section(body=section.body, structure=new_structure))
        db_session.add(SectionSynopsis(body=synopsis.body, structure=new_structure))
        db_session.add(SectionNotes(body=notes.body, structure=new_structure))


@app.route('/add_node/<int:project_id>', methods=['POST'])
def add_node(project_id):
    '''
    Add a new node to the tree and pass the created data back to the caller so it can add
    it to the tree in the browser.
    '''
    nodes = request.get_json()
    parent_id = nodes.get('parent')
    project = Project.query.filter_by(id=project_id).first()
    parent = Structure.query.filter_by(id=parent_id).first()
    # Get the highest display order for this project so we can assign the new node to last place.
    displayorder = db_session.query(Structure.displayorder, func.max(Structure.displayorder)).filter_by(id=project_id).scalar() + 1
    
    structure = create_node(project=project, parent=parent, displayorder=displayorder)
    
    db_session.commit()

    return jsonify(id=structure.id, 
                   text=structure.title, 
                   displayorder=structure.displayorder, 
                   status_text=gettext("Hoorah! Section was added."))
    
    
def create_node(project, parent=None, displayorder=1, title='New Section'):
    '''
    Create a new node along with anything that has to be attached.
    '''
    structure = Structure(parent=parent, title=title, displayorder=displayorder, project=project)
    db_session.add(structure)
    db_session.add(Section(body="", structure=structure))
    db_session.add(SectionSynopsis(body="", structure=structure))
    db_session.add(SectionNotes(body="", structure=structure))
    return structure


@app.route('/delete_node', methods=['POST'])
def delete_node():
    '''
    Delete the node and associated section text.
    '''
    nodes = request.get_json().get('ids')
    for node_id in nodes:
        section = Section.query.filter_by(structure_id=node_id).first()
        db_session.delete(section)
        structure = Structure.query.filter_by(id=node_id).first()
        db_session.delete(structure)
        db_session.commit()

    return jsonify(status_text=gettext("Hoorah! Section was deleted."))


@app.route('/update_node', methods=['POST'])
def update_node():
    '''
    Update the node.
    '''
    node = request.get_json()
    node_id = node.get('id')
    node_text = node.get('text')

    structure = Structure.query.filter_by(id=node_id).first()
    structure.title = node_text
    db_session.commit()

    return jsonify(status_text=gettext("Hoorah! Section was updated."))


@app.route('/update_section', methods=['POST'])
def update_section():
    section = Section.query.filter(Section.id == request.form['section_id']).first()
    section.body = request.form['sectiontext']
    db_session.commit()
    
    return jsonify(status=True, 
                   status_text=gettext("Save was a Complete Success!"))


@app.route('/update_synopsis', methods=['POST'])
def update_synopsis():
    
    synopsis = SectionSynopsis.query.filter(SectionSynopsis.id == request.form['synopsis_id']).first()
    synopsis.body = request.form['synopsis_text']
    db_session.commit()
    return jsonify(status=True, 
                   status_text=gettext("Hoorah! Synopsis was updated."))


@app.route('/update_notes', methods=['POST'])
def update_notes():
    
    notes = SectionNotes.query.filter(SectionNotes.id == request.form['notes_id']).first()
    notes.body = request.form['notes_text']
    db_session.commit()
    return jsonify(status=True, 
                   status_text=gettext("Hoorah! Notes was updated."))


@app.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    
    form = ProjectForm(request.form)
    del form.template
    if form.validate():
        project = Project.query.filter_by(id=project_id).first()
        project.name = form.name.data
        project.description = form.description.data
        project.is_template = form.is_template.data
        db_session.commit()
        return jsonify(status=True, status_text=gettext("Hoorah! Project details were updated."))

    # Return the errors so that the caller can show them without refreshing
    # the page.    
    return jsonify(status=False, 
                   name_errors=form.name.errors, 
                   description_errors=form.description.errors)


@app.route('/export_project/<int:project_id>', methods=['GET'])
def export_project(project_id):
    '''
    Export the project to a file for the user to download.
    It will be a basic dump to start with to show the idea.
    '''
    def generate():
        for instance in db_session.query(Structure).filter_by(project_id=project_id).order_by(Structure.displayorder):
            section = Section.query.filter_by(structure_id=instance.id).first()
            yield section.body
    
    # add a filename
    project = Project.query.filter_by(id=project_id).first()
    headers = Headers()
    headers.add('Content-Disposition', 'attachment', filename=(project.name + '.html'))

    # stream the response as the data is generated
    # default mimetype is text/html which is what we want in this case.
    return Response(
        stream_with_context(generate()),
        headers=headers
    )

    
@app.route('/show_config')
def show_config():
    '''
    Get the current the current configuration and then show the template.
    '''
    config = Project.query.all()
    return render_template('config.html', 
                           config=config)


@app.route('/save_config', methods=['POST'])
def save_config():

    flash(gettext('Configuration Save was a Complete Success!'))
    return redirect(url_for('show_config'))

#@crsf.error_handler
#def csrf_error(reason):
#    return render_template('csrf_error.html', reason=reason), 400