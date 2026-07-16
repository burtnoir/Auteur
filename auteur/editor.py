from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Response, session, current_app,
    stream_with_context
)
from werkzeug.datastructures import Headers
from auteur.models import db, Project, Structure, Section, SectionSynopsis, SectionNotes, SectionCharacters
from flask_babel import gettext, Babel
from flask.json import jsonify
from flask_weasyprint import HTML, render_pdf
from auteur.forms import ProjectForm
import markdown

bp = Blueprint('editor', __name__)


@bp.route('/')
@bp.route('/get_project_list', methods=['GET'])
def get_project_list():
    projects = Project.query.filter(Project.is_deleted == False, Project.is_template == False).all()
    return get_project_list_helper(projects)


@bp.route('/get_template_list', methods=['GET'])
def get_template_list():
    projects = Project.query.filter(Project.is_deleted == False, Project.is_template == True).all()
    return get_project_list_helper(projects)


@bp.route('/get_deleted_template_list', methods=['GET'])
def get_deleted_template_list():
    projects = Project.query.filter(Project.is_deleted == True, Project.is_template == True).all()
    return get_project_list_helper(projects)


@bp.route('/get_deleted_project_list', methods=['GET'])
def get_deleted_project_list():
    """
    Get a list of deleted projects for display.
    """
    projects = Project.query.filter(Project.is_deleted == True, Project.is_template == False).all()
    return get_project_list_helper(projects)


def get_project_list_helper(projects):
    session.pop('project_id', None)
    form = ProjectForm(request.form)
    form.template.choices = [(t.id, t.name) for t in Project.query.filter(Project.is_template == True, Project.is_deleted == False).order_by('name').all()]
    form.template.choices.insert(0, (0, gettext('-- Choose a Template --')))
    return render_template('editor/index.jinja',
                           projects=projects,
                           form=form)


@bp.route('/project/<int:project_id>/', defaults={'structure_id': None})
@bp.route('/project/<int:project_id>/<int:structure_id>')
def show_content(project_id, structure_id):
    # show the project with the given id, the id is an integer
    project = Project.query.filter_by(id=project_id).first()
    form = ProjectForm(obj=project)
    del form.template
    del form.submit
    structure = Structure.query.filter_by(project_id=project.id)

    # If the id wasn't passed (probably because the call is from the project page)
    # then open the first structure item's text.
    if structure_id is None:
        structure_id = structure[0].id
    section = Section.query.filter_by(structure_id=structure_id).first()
    sectionchildren = Section.query.filter_by(structure_id=structure_id).first()
    synopsis = SectionSynopsis.query.filter_by(structure_id=structure_id).first()
    notes = SectionNotes.query.filter_by(structure_id=structure_id).first()
    characters = SectionCharacters.query.filter_by(structure_id=structure_id).first()
    # TODO Decide if setting a session key-value is needed - was using it for the project form validator
    # but I have a different way to do it now where the project_id is stored on the
    # project form so we might not need to use the session.  Probably better
    # as it avoids making the project id global which needs managing compared to
    # a property on the form which will only live for the life of the object instance.
    # session['project_id'] = project_id
    return render_template('editor/content.jinja',
                           project=project,
                           structure=structure,
                           section=section,
                         #  sectionchildren=markdown.markdown(sectionchildren),
                           sectionchildren=sectionchildren,
                           synopsis=synopsis,
                           notes=notes,
                           characters=characters,
                           form=form)


def collect_descendant_section_text(structure_id, text_parts):
    """
    Recursively walk the descendants of the given structure node, appending
    each one's section text to text_parts in the same order as the node
    hierarchy (i.e. a depth-first walk, with each level ordered by
    displayorder - the same ordering used to build the tree in content.jinja).
    """
    children = Structure.query.filter_by(parent_id=structure_id).order_by(Structure.displayorder).all()
    for child in children:
        section = Section.query.filter_by(structure_id=child.id).first()
        if section and section.body:
            text_parts.append(section.body)
        # Recurse into this child's own descendants before moving on to the
        # next sibling, so the result reflects the tree's depth-first order.
        collect_descendant_section_text(child.id, text_parts)


def get_descendant_section_text(structure_id):
    """
    Get the concatenated text of all descendants of the given structure node,
    with each piece separated by a blank line for readability.
    """
    text_parts = []
    collect_descendant_section_text(structure_id, text_parts)
    return '\n\n'.join(text_parts)


@bp.route('/get_section', methods=['GET'])
def get_section():
    """
    Get the contents of a section for display.
    """
    structure_id = request.args.get('structure_id', 0, type=int)
    section = Section.query.filter_by(structure_id=structure_id).first()
    synopsis = SectionSynopsis.query.filter_by(structure_id=structure_id).first()
    notes = SectionNotes.query.filter_by(structure_id=structure_id).first()
    characters = SectionCharacters.query.filter_by(structure_id=structure_id).first()
    return jsonify(section_text=section.body,
                   section_id=section.id,
                   section_children_text=markdown.markdown(get_descendant_section_text(structure_id)),
                   synopsis_text=synopsis.body,
                   synopsis_id=synopsis.id,
                   notes_text=notes.body,
                   notes_id=notes.id,
                   characters_text=characters.body,
                   characters_id=characters.id)


@bp.route('/add_project', methods=['POST'])
def add_project():
    """
    Add a project.  Default a tree structure and sections to go with them.
    """
    session.pop('project_id', None)
    form = ProjectForm(request.form)
    form.template.choices = [(t.id, t.name) for t in Project.query.order_by('name').filter(Project.is_template)]
    form.template.choices.insert(0, (0, gettext('-- Choose a Template --')))
    if form.validate():
        project = Project(name=form.name.data, description=form.description.data, is_template=form.is_template.data)
        db.session.add(project)

        if form.template.data != 0:
            copy_from_template(project, form.template.data)
        else:
            create_node(project=project, title=form.name.data)

        db.session.commit()
        session['project_id'] = project.id

        flash('New Project Added')
        return redirect(url_for('editor.show_content', project_id=project.id, structure_id=None))

    projects = Project.query.all()
    return render_template('editor/index.jinja',
                           projects=projects,
                           form=form)


def copy_from_template(project, template_id):
    """
    Get the template contents and add them to the new project.
    """
    structure_map = {}
    for structure, section, synopsis, notes, characters in db.session.query(Structure, Section, SectionSynopsis,
                                                                SectionNotes, SectionCharacters).filter(
        Structure.id == Section.structure_id).filter(Structure.id == SectionSynopsis.structure_id).filter(
        Structure.id == SectionNotes.structure_id).filter(Structure.id == SectionCharacters.structure_id).filter(
        Structure.project_id == template_id).order_by(
        Structure.parent_id).all():

        # Check the map to find the new parent.
        new_parent = None
        if structure.parent and structure.parent_id in structure_map:
            new_parent = structure_map[structure.parent_id]
        # Create the new structure element using the discovered parent.  If nothing was found
        # then it has no parent and so is a root element.
        new_structure = Structure(parent=new_parent, title=structure.title, displayorder=structure.displayorder,
                                  project=project)
        db.session.add(new_structure)
        # Every time a structure record is processed we add it to the map to link the
        # template element to the newly created element.
        structure_map[structure.id] = new_structure
        db.session.add(Section(body=section.body, structure=new_structure))
        db.session.add(SectionSynopsis(body=synopsis.body, structure=new_structure))
        db.session.add(SectionNotes(body=notes.body, structure=new_structure))
        db.session.add(SectionCharacters(body=characters.body, structure=new_structure))


@bp.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    """"
    Delete the project.
    """
    project = Project.query.filter(Project.id == project_id).first()
    project.is_deleted = True
    db.session.commit()

    return jsonify(status=True, status_text=gettext("Hoorah! Project was deleted."))


@bp.route('/undelete_project/<int:project_id>', methods=['POST'])
def undelete_project(project_id):
    """
    Undelete the project.
    """
    project = Project.query.filter(Project.id == project_id).first()
    project.is_deleted = False
    db.session.commit()

    return jsonify(status=True, status_text=gettext("Hoorah! Project was undeleted."))


@bp.route('/add_node/<int:project_id>', methods=['POST'])
def add_node(project_id):
    """
    Add a new node to the tree and pass the created data back to the caller so it can add
    it to the tree in the browser.
    """
    nodes = request.get_json()
    parent_id = nodes.get('parent')
    project = Project.query.filter(Project.id == project_id).first()
    parent = Structure.query.filter(Structure.id == parent_id).first()
    # Get the highest display order for this project so we can assign the new node to last place.
    max_display_order = db.session.query(db.func.max(Structure.displayorder)).filter(Structure.project_id == project_id).scalar()
    displayorder = (max_display_order or 0) + 1

    structure = create_node(project=project, parent=parent, displayorder=displayorder)

    db.session.commit()

    return jsonify(id=structure.id,
                   text=structure.title,
                   displayorder=structure.displayorder,
                   status_text=gettext("Hoorah! Section was added."))


def create_node(project, parent=None, displayorder=1, title='New Section'):
    """
    Create a new node along with anything that has to be attached.
    """
    structure = Structure(parent=parent, title=title, displayorder=displayorder, project=project)
    db.session.add(structure)
    db.session.add(Section(body="", structure=structure))
    db.session.add(SectionSynopsis(body="", structure=structure))
    db.session.add(SectionNotes(body="", structure=structure))
    db.session.add(SectionCharacters(body="", structure=structure))
    return structure


@bp.route('/delete_node', methods=['POST'])
def delete_node():
    """
    Delete the node and associated section text.
    """
    nodes = request.get_json().get('ids')
    for node_id in nodes:
        section = Section.query.filter_by(structure_id=node_id).first()
        db.session.delete(section)
        structure = Structure.query.filter_by(id=node_id).first()
        db.session.delete(structure)
        db.session.commit()

    return jsonify(status_text=gettext("Hoorah! Section was deleted."))


@bp.route('/update_node', methods=['POST'])
def update_node():
    """
    Update the node text.
    """
    node = request.get_json()
    node_id = node.get('id')
    node_text = node.get('text')

    structure = Structure.query.filter_by(id=node_id).first()
    structure.title = node_text
    db.session.commit()

    return jsonify(status_text=gettext("Hoorah! Section was updated."))


@bp.route('/update_section', methods=['POST'])
def update_section():
    section = db.get_or_404(Section, request.form['section_id'])
    section.body = request.form['section_text']
    db.session.commit()

    return jsonify(status=True,
                   status_text=gettext("Section save was a Complete Success!"))


@bp.route('/update_synopsis', methods=['POST'])
def update_synopsis():
    synopsis = SectionSynopsis.query.filter(SectionSynopsis.id == request.form['synopsis_id']).first()
    synopsis_text = request.form.get('synopsis_text')
    if synopsis_text is None:
        return jsonify(status=False,
                       status_text=gettext("Synopsis text is missing - no update was done."))
    synopsis.body = synopsis_text
    db.session.commit()
    return jsonify(status=True,
                   status_text=gettext("Hoorah! Synopsis was updated."))


@bp.route('/update_notes', methods=['POST'])
def update_notes():
    notes = SectionNotes.query.filter(SectionNotes.id == request.form['notes_id']).first()
    notes_text = request.form.get('notes_text')
    if notes_text is None:
        return jsonify(status=False,
                       status_text=gettext("Notes text is missing - no update was done."))
    notes.body = notes_text
    db.session.commit()
    return jsonify(status=True,
                   status_text=gettext("Hoorah! Notes was updated."))


@bp.route('/update_characters', methods=['POST'])
def update_characters():
    characters = SectionCharacters.query.filter(SectionCharacters.id == request.form['character_id']).first()
    characters_text = request.form.get('character_text')
    if characters_text is None:
        return jsonify(status=False,
                       status_text=gettext("Characters text is missing - no update was done."))
    characters.body = characters_text
    db.session.commit()
    return jsonify(status=True,
                   status_text=gettext("Hoorah! Characters was updated."))


@bp.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    form = ProjectForm()
    del form.template
    form.id.data = str(project_id)
    if form.validate_on_submit():
        project = Project.query.filter(Project.id == project_id).first()
        project.name = form.name.data
        project.description = form.description.data
        project.is_template = form.is_template.data
        db.session.commit()
        return jsonify(status=True, status_text=gettext("Hoorah! Project details were updated."))

    # Return the errors so that the caller can show them without refreshing
    # the page.
    return jsonify(status=False,
                   name_errors=form.name.errors,
                   description_errors=form.description.errors)


@bp.route('/export_project/<int:project_id>', methods=['GET'])
def export_project(project_id):
    """
    Export the project to a file for the user to download.
    It will be a basic dump to start with to show the idea.
    """
    project = Project.query.filter(Project.id == project_id).first()
    headers = Headers()
    # add a filename
    headers.add('Content-Disposition', 'attachment', filename=(project.name + '.html'))

    # stream the response as the data is generated
    # default mimetype is text/html which is what we want in this case.
    return Response(
        stream_with_context(generate(project_id)),
        headers=headers
    )


@bp.route('/export_project_pdf/<int:project_id>', methods=['GET'])
def export_project_pdf(project_id):
    """
    Make a PDF straight from HTML in a string and send it to the user.
    """
    html = ''
    for value in generate(project_id):
        html += value
    return render_pdf(HTML(string=html))


def generate(project_id):
    for instance in db.session.query(Structure).filter(Structure.project_id == project_id).order_by(
            Structure.displayorder):
        section = Section.query.filter(Section.structure_id == instance.id).first()
        yield section.body


@bp.route('/show_config')
def show_config():
    """
    Get the current the current configuration and then show the template.
    """
    config = Project.query.all()
    return render_template('editor/config.jinja',
                           config=config)


@bp.route('/save_config', methods=['POST'])
def save_config():
    flash(gettext('Configuration Save was a Complete Success!'))
    return redirect(url_for('editor.show_config'))

# @csrf.error_handler
# def csrf_error(reason):
#     return render_template('csrf_error.jinja', reason=reason), 400