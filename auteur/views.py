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


@app.route('/')
def list_projects():
    form = ProjectForm(request.form)
    form.template.choices = [(t.id, t.name) for t in Project.query.order_by('name').filter(Project.is_template)]
    projects = Project.query.all()
    return render_template('index.html', 
                           projects=projects, 
                           form=form)


@app.route('/project/<int:project_id>/', defaults={'structure_id' : None})
@app.route('/project/<int:project_id>/<int:structure_id>')
def show_content(project_id, structure_id):
    # show the project with the given id, the id is an integer
    project = Project.query.filter_by(id=project_id).first()
    form = ProjectForm(obj=project)
    form.template.choices = [(t.id, t.name) for t in Project.query.order_by('name').filter(Project.is_template)]
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
    if form.validate():
        project = Project(name=form.name.data, description=form.description.data, is_template=form.is_template.data)
        db_session.add(project)
               
        structure = create_node(project=project, title=form.name.data)
        
        db_session.commit()
    
        flash('New Project Added')
        return redirect(url_for('show_content', project_id=project.id, structure_id=structure.id))
    
    projects = Project.query.all()
    return render_template('index.html', 
                           projects=projects, 
                           form=form)


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
                   status_text="Hoorah! Section was added.")
    
    
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

    return jsonify(status_text="Hoorah! Section was deleted.")


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

    return jsonify(status_text="Hoorah! Section was updated.")


@app.route('/update_section', methods=['POST'])
def update_section():
    section = Section.query.filter(Section.id == request.form['section_id']).first()
    section.body = request.form['sectiontext']
    db_session.commit()

    return jsonify(status=True, 
                   status_text="Save was a Complete Success!")


@app.route('/update_synopsis', methods=['POST'])
def update_synopsis():
    
    synopsis = SectionSynopsis.query.filter(SectionSynopsis.id == request.form['synopsis_id']).first()
    synopsis.body = request.form['synopsis_text']
    db_session.commit()
    return jsonify(status=True, 
                   status_text="Hoorah! Synopsis was updated.")


@app.route('/update_notes', methods=['POST'])
def update_notes():
    
    notes = SectionNotes.query.filter(SectionNotes.id == request.form['notes_id']).first()
    notes.body = request.form['notes_text']
    db_session.commit()
    return jsonify(status=True, 
                   status_text="Hoorah! Notes was updated.")


@app.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    
    form = ProjectForm(request.form)
    if form.validate():
        project = Project.query.filter_by(id=project_id).first()
        project.name = request.form['name']
        project.description = request.form['description']
        if request.form['is_template'] == 'y':
            project.is_template = True
        else:
            project.is_template = False
        db_session.commit()
        return jsonify(status=True, status_text="Hoorah! Project details were updated.")

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

    flash('Configuration Save was a Complete Success!')
    return redirect(url_for('show_config'))

#@crsf.error_handler
#def csrf_error(reason):
#    return render_template('csrf_error.html', reason=reason), 400