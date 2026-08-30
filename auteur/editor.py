from datetime import datetime

import markdown
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, Response, session, current_app,
    abort
)
from flask.json import jsonify
from flask_babel import gettext
from flask_login import current_user
from flask_weasyprint import HTML, render_pdf
from flask_wtf.csrf import CSRFError
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.datastructures import Headers

from auteur.forms import ProjectForm, ConfigurationForm, CheckpointForm, RestorepointForm
from auteur.models import db, Project, Structure, Section, SectionSynopsis, SectionNotes, SectionCharacters, \
    Configuration, CheckpointSection, Checkpoint

bp = Blueprint('editor', __name__)


@bp.before_request
def require_login():
    """
    Every route in this blueprint deals with a specific user's projects,
    so nothing here should be reachable while logged out.
    """
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()
    return None


# ---------------------------------------------------------------------------
# Ownership helpers
#
# Project has a user_id directly. Structure, Section, SectionSynopsis,
# SectionNotes and SectionCharacters don't - they only get to a user by
# walking back up to Structure.project.user_id. These helpers centralise
# that check so every route uses the same rule, and 404 (rather than 403)
# on a mismatch so we don't confirm to a user that another user's project
# id/structure id even exists.
# ---------------------------------------------------------------------------

def get_owned_project_or_404(project_id):
    return Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()


def get_owned_structure_or_404(structure_id):
    return (Structure.query
            .join(Project, Structure.project_id == Project.id)
            .filter(Structure.id == structure_id, Project.user_id == current_user.id)
            .first_or_404())


def check_section_owner_or_404(section):
    """
    Section/SectionSynopsis/SectionNotes/SectionCharacters all share this
    shape: they have .structure, which has .project, which has .user_id.
    Use this after a db.get_or_404 lookup by primary key, since that lookup
    on its own doesn't check ownership.
    """
    if section is None or section.structure.project.user_id != current_user.id:
        abort(404)
    return section


def get_owned_checkpoint_or_404(checkpoint_id):
    return (Checkpoint.query
            .join(Project, Checkpoint.project_id == Project.id)
            .filter(Checkpoint.id == checkpoint_id, Project.user_id == current_user.id)
            .first_or_404())


@bp.route('/')
@bp.route('/get_project_list', methods=['GET'])
def get_project_list():
    projects = Project.query.filter(Project.is_deleted == False, Project.is_template == False,
                                    Project.user_id == current_user.id).all()
    return get_project_list_helper(projects)


@bp.route('/get_template_list', methods=['GET'])
def get_template_list():
    projects = Project.query.filter(Project.is_deleted == False, Project.is_template == True,
                                    Project.user_id == current_user.id).all()
    return get_project_list_helper(projects)


@bp.route('/get_deleted_template_list', methods=['GET'])
def get_deleted_template_list():
    projects = Project.query.filter(Project.is_deleted == True, Project.is_template == True,
                                    Project.user_id == current_user.id).all()
    return get_project_list_helper(projects)


@bp.route('/get_deleted_project_list', methods=['GET'])
def get_deleted_project_list():
    """
    Get a list of deleted projects for display.
    """
    projects = Project.query.filter(Project.is_deleted == True, Project.is_template == False,
                                    Project.user_id == current_user.id).all()
    return get_project_list_helper(projects)


def get_project_list_helper(projects):
    session.pop('project_id', None)
    config = Configuration.query.filter_by(id=1).first()
    form = ProjectForm(request.form)
    # Templates are per-user too, so only offer the current user's own templates
    # as choices when starting a new project.
    form.template.choices = [(t.id, t.name) for t in Project.query.filter(
        Project.is_template == True, Project.is_deleted == False,
        Project.user_id == current_user.id).order_by('name').all()]
    form.template.choices.insert(0, (0, gettext('-- Choose a Template --')))
    return render_template('editor/project_list.jinja',
                           projects=projects,
                           config=config,
                           form=form)


@bp.route('/project/<int:project_id>/', defaults={'structure_id': None})
@bp.route('/project/<int:project_id>/<int:structure_id>')
def show_content(project_id, structure_id):
    config = Configuration.query.filter_by(id=1).first()
    # show the project with the given id, the id is an integer
    project = get_owned_project_or_404(project_id)
    form = ProjectForm(obj=project)
    del form.template
    del form.submit

    # Create the checkpoint form at the same time so it can be used if needed.
    checkpoint_form = CheckpointForm()
    checkpoint_form.project_id.data = project.id
    restorepoint_form = RestorepointForm()
    restorepoint_form.project_id.data = project_id

    # If the id wasn't passed (probably because the call is from the project page)
    # then open the first structure item's text.
    if structure_id is None:
        structure = Structure.query.filter_by(project_id=project.id, parent_id=None).first()
        structure_id = structure.id
    else:
        # structure_id came from the URL - make sure it actually belongs to
        # this project/user rather than trusting it blindly.
        get_owned_structure_or_404(structure_id)
    section = Section.query.filter_by(structure_id=structure_id).first()
    synopsis = SectionSynopsis.query.filter_by(structure_id=structure_id).first()
    notes = SectionNotes.query.filter_by(structure_id=structure_id).first()
    characters = SectionCharacters.query.filter_by(structure_id=structure_id).first()

    return render_template('editor/content.jinja',
                           config=config,
                           project=project,
                           section=section,
                           section_children_text=markdown.markdown(get_descendant_section_text(structure_id)),
                           synopsis=synopsis,
                           notes=notes,
                           characters=characters,
                           form=form,
                           checkpoint_form=checkpoint_form,
                           restorepoint_form=restorepoint_form)


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

def build_export_sections(project_id):
    """
    Walk the whole project tree in document order (depth-first, respecting
    displayorder at each level) and return a flat list of
    {'title', 'body_html', 'level'} dicts ready for the export template.
    """
    sections = []
    config = Configuration.query.filter_by(id=1).first()

    def add(structure, level, export_node_titles):
        section = Section.query.filter_by(structure_id=structure.id).first()
        text_block = {
            'title': structure.title if export_node_titles else '',
            'body_html': markdown.markdown(section.body) if section and section.body else '',
            'level': level,
        }
        # Only add a section if there is some text there.
        if text_block['title'] != '' or text_block['body_html'] != '':
            sections.append(text_block)
        for child in Structure.query.filter_by(parent_id=structure.id).order_by(Structure.displayorder).all():
            add(child, level + 1, config.export_node_titles)

    root = Structure.query.filter_by(project_id=project_id, parent_id=None).first()
    if root:
        add(root, 0, config.export_node_titles)

    return sections

def create_tree_item_children(children):
    tree_item_children = []
    for child in children:
        tree_item_children.append(
            {"id": child.id, "key": child.id, "title": child.title, "type": "folder", "expanded": False, "children": create_tree_item_children(child.children)})
    return tree_item_children

@bp.route('/get_project_tree', methods=['GET'])
def get_project_tree():
    """
    Get the project tree.
    """
    project_id = request.args.get('project_id', 0, type=int)
    # Confirms this project belongs to the current user before we hand back
    # any of its tree structure.
    get_owned_project_or_404(project_id)
    structure = Structure.query.filter_by(project_id=project_id).first()
    tree_data = {"types": {
        "book": {"icon": "fa-solid fa-book"},
        "chapter": {"icon": "fa-solid fa-folder", "classes": "bold-style"}
    }, "children": [{"id": structure.id, "key": structure.id, "title": structure.title, "type": "book", "expanded": True,
                     "children": create_tree_item_children(structure.children)}]}

    return jsonify(tree_data)


@bp.route('/get_section', methods=['GET'])
def get_section():
    """
    Get the contents of a section for display.
    """
    structure_id = request.args.get('structure_id', 0, type=int)
    # structure_id is client-supplied - verify it's owned by this user before
    # returning any of its text.
    get_owned_structure_or_404(structure_id)
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
    # Only the current user's own templates should be offered/usable as a
    # source to copy from.
    form.template.choices = [(t.id, t.name) for t in Project.query.filter(
        Project.is_template == True, Project.user_id == current_user.id).order_by('name').all()]
    form.template.choices.insert(0, (0, gettext('-- Choose a Template --')))
    if form.validate():
        project = Project(name=form.name.data, description=form.description.data,
                          is_template=form.is_template.data, user=current_user)
        db.session.add(project)

        if form.template.data != 0:
            # get_owned_project_or_404 makes sure a user can't copy from a
            # template id that isn't theirs, just by editing the posted form.
            template_project = get_owned_project_or_404(form.template.data)
            copy_from_template(project, template_project.id)
        else:
            create_node(project=project, title=form.name.data)

        db.session.commit()
        session['project_id'] = project.id

        flash('New Project Added')
        return redirect(url_for('editor.show_content', project_id=project.id, structure_id=None))

    projects = Project.query.all()
    return render_template('editor/project_list.jinja',
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
    project = get_owned_project_or_404(project_id)
    project.is_deleted = True
    db.session.commit()

    return jsonify(status=True, status_text=gettext("Hoorah! Project was deleted."))


@bp.route('/undelete_project/<int:project_id>', methods=['POST'])
def undelete_project(project_id):
    """
    Undelete the project.
    """
    project = get_owned_project_or_404(project_id)
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
    project = get_owned_project_or_404(project_id)
    parent = Structure.query.filter(Structure.id == parent_id).first()
    # Get the highest display order for this project so we can assign the new node to last place.
    max_display_order = db.session.query(db.func.max(Structure.displayorder)).filter(Structure.project_id == project_id).scalar()
    displayorder = (max_display_order or 0) + 1

    structure = create_node(project=project, parent=parent, displayorder=displayorder)

    db.session.commit()

    return jsonify(children = [{"id": structure.id, "key": structure.id, "title": structure.title, "type": "book", "expanded": True, "children": []}],
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
    Delete the node and associated section text.  This will cascade to the descendants.
    """
    node_id = request.get_json().get('id')
    structure = get_owned_structure_or_404(node_id)
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

    # Previously this looked the node up with no ownership check at all,
    # so any logged-in user could rename any node by id.
    structure = get_owned_structure_or_404(node_id)
    structure.title = node_text
    db.session.commit()

    return jsonify(status_text=gettext("Hoorah! Section was updated."))


@bp.route('/update_section', methods=['POST'])
def update_section():
    section = db.get_or_404(Section, request.form['section_id'])
    check_section_owner_or_404(section)
    section.body = request.form['section_text']
    conflict = commit_with_conflict_check(
        gettext("Someone else saved changes to this section. Refresh to see the latest version."))
    if conflict:
        return conflict

    return jsonify(status=True,
                   status_text=gettext("Section save was a Complete Success!"))


@bp.route('/update_synopsis', methods=['POST'])
def update_synopsis():
    synopsis = SectionSynopsis.query.filter(SectionSynopsis.id == request.form['synopsis_id']).first()
    check_section_owner_or_404(synopsis)
    synopsis_text = request.form.get('synopsis_text')
    if synopsis_text is None:
        return jsonify(status=False,
                       status_text=gettext("Synopsis text is missing - no update was done."))
    synopsis.body = synopsis_text
    conflict = commit_with_conflict_check(
        gettext("Someone else saved changes to these synopsis notes. Refresh to see the latest version."))
    if conflict:
        return conflict
    return jsonify(status=True,
                   status_text=gettext("Hoorah! Synopsis was updated."))


@bp.route('/update_notes', methods=['POST'])
def update_notes():
    notes = SectionNotes.query.filter(SectionNotes.id == request.form['notes_id']).first()
    check_section_owner_or_404(notes)
    notes_text = request.form.get('notes_text')
    if notes_text is None:
        return jsonify(status=False,
                       status_text=gettext("Notes text is missing - no update was done."))
    notes.body = notes_text
    conflict = commit_with_conflict_check(
        gettext("Someone else saved changes to these notes. Refresh to see the latest version."))
    if conflict:
        return conflict
    return jsonify(status=True,
                   status_text=gettext("Hoorah! Notes was updated."))


@bp.route('/update_characters', methods=['POST'])
def update_characters():
    characters = SectionCharacters.query.filter(SectionCharacters.id == request.form['character_id']).first()
    check_section_owner_or_404(characters)
    characters_text = request.form.get('character_text')
    if characters_text is None:
        return jsonify(status=False,
                       status_text=gettext("Characters text is missing - no update was done."))
    characters.body = characters_text
    conflict = commit_with_conflict_check(
        gettext("Someone else saved changes to these character notes. Refresh to see the latest version."))
    if conflict:
        return conflict
    return jsonify(status=True,
                   status_text=gettext("Hoorah! Characters was updated."))


def commit_with_conflict_check(conflict_message):
    """
    Commit the session, translating a StaleDataError into a friendly
    jsonify response instead of letting it propagate as a 500.
    Returns None on success, or a Flask response to return immediately
    if there was a conflict.
    """
    try:
        db.session.commit()
        return None
    except StaleDataError:
        db.session.rollback()
        return jsonify(status=False, status_text=conflict_message)


@bp.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    # Confirms ownership before any form processing touches the project.
    project = get_owned_project_or_404(project_id)
    form = ProjectForm()
    del form.template
    form.id.data = str(project_id)
    if form.validate_on_submit():
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
    project = get_owned_project_or_404(project_id)
    html = render_template('editor/export.jinja', project=project,
                           sections=build_export_sections(project_id))
    headers = Headers()
    headers.add('Content-Disposition', 'inline', filename=(project.name + '.html'))
    return Response(html, headers=headers)


@bp.route('/export_project_pdf/<int:project_id>', methods=['GET'])
def export_project_pdf(project_id):
    project = get_owned_project_or_404(project_id)
    html = render_template('editor/export.jinja', project=project,
                           sections=build_export_sections(project_id))
    return render_pdf(HTML(string=html))


@bp.route('/show_config', defaults={'config_id': 1})
@bp.route('/show_config/<int:config_id>/')
def show_config(config_id):
    """
    Get the current the current configuration and then show the configuration form template.
    Configuration is global (not per-project/per-user), so no ownership
    check is needed here beyond being logged in.
    """
    config = Configuration.query.filter_by(id=config_id).first()
    form = ConfigurationForm(obj=config)
    return render_template('editor/config.jinja',
                           config=config,
                           form=form)


@bp.route('/save_config', methods=['POST'])
def save_config():
    """
    Save the configuration
    :return:
    """
    session.pop('project_id', None)
    form = ConfigurationForm(request.form)

    if form.validate():
        configuration = Configuration.query.filter_by(id=form.id.data).first()
        if configuration is None:
            configuration = Configuration(theme=form.theme.data)
            db.session.add(configuration)
        else:
            configuration.theme = form.theme.data
            configuration.export_node_titles = form.export_node_titles.data
        db.session.commit()
        flash(gettext('Configuration Save was a Complete Success!'))
        return redirect(url_for('editor.show_config'))

    configuration = Configuration.query.filter_by(id=form.id.data).first()
    return render_template('editor/config.jinja', config=configuration, form=form)


@bp.route('/create_checkpoint', methods=['POST'])
def create_checkpoint():
    """
    Create a checkpoint for a project
    :return:
    """
    form = CheckpointForm()
    project_id = form.project_id.data
    get_owned_project_or_404(project_id)
    if form.validate_on_submit():
        label = form.label.data or gettext('Checkpoint')
        checkpoint = create_checkpoint_internal(label, project_id)
        return jsonify(status=True, checkpoint_id=checkpoint.id,
                       status_text=gettext("Checkpoint '%(label)s' created.", label=label))
    return jsonify(status=False, label_errors=form.label.errors)


def create_checkpoint_internal(label: str, project_id) -> Checkpoint:
    """
    Create a checkpoint for a project
    :param label: The user defined name of the project checkpoint
    :param project_id: The unique identifier for the project
    :return: Checkpoint
    """
    get_owned_project_or_404(project_id)
    checkpoint = Checkpoint(project_id=project_id, label=label, user=current_user)
    db.session.add(checkpoint)

    structures = Structure.query.filter_by(project_id=project_id).all()
    for structure in structures:
        db.session.add(CheckpointSection(
            checkpoint=checkpoint,
            structure_id=structure.id,
            parent_id=structure.parent_id,
            displayorder=structure.displayorder,
            title=structure.title,
            section_body=structure.section.body if structure.section else '',
            synopsis_body=structure.sectionsynopsis.body if structure.sectionsynopsis else '',
            notes_body=structure.sectionnotes.body if structure.sectionnotes else '',
            characters_body=structure.sectioncharacters.body if structure.sectioncharacters else '',
        ))

    db.session.commit()
    return checkpoint


@bp.route('/restore_checkpoint', methods=['POST'])
def restore_checkpoint():
    """
    Restore a checkpoint of a project. Any node that's been deleted since the
    checkpoint was taken is recreated (with its original title/text and its
    original place in the tree) rather than silently skipped - including,
    recursively, any ancestor of that node that was also deleted, since a
    whole deleted subtree needs its parent chain rebuilt before a child can
    be reattached to it.
    :return:
    """
    form = RestorepointForm()
    checkpoint_id = form.check_point.data
    checkpoint = get_owned_checkpoint_or_404(checkpoint_id)

    # Safety net: snapshot current state before overwriting it.
    create_checkpoint_internal(gettext("Auto-save before restoring %(label)s at %(current_date)s",
                                       label=checkpoint.label,
                                       current_date=datetime.now().isoformat(sep=" ", timespec="seconds")), checkpoint.project_id)

    # Keyed by the *original* structure_id from checkpoint time, so a child
    # row can find its parent's checkpoint snapshot even though the parent
    # may need to be recreated (and will get a brand new id when it is).
    cs_by_structure_id = {cs.structure_id: cs for cs in checkpoint.sections}
    # original structure_id -> live Structure row, filled in as we go so
    # each node (existing or recreated) is only resolved once.
    resolved = {}

    def restore_or_recreate(cs):
        if cs.structure_id in resolved:
            return resolved[cs.structure_id]

        structure = Structure.query.filter_by(id=cs.structure_id).first()
        if structure is not None:
            structure.title = cs.title
            if structure.section:
                structure.section.body = cs.section_body
            if structure.sectionsynopsis:
                structure.sectionsynopsis.body = cs.synopsis_body
            if structure.sectionnotes:
                structure.sectionnotes.body = cs.notes_body
            if structure.sectioncharacters:
                structure.sectioncharacters.body = cs.characters_body
            resolved[cs.structure_id] = structure
            return structure

        # Node was deleted since the checkpoint was taken - recreate it,
        # first recursively recreating its parent if that was deleted too.
        parent = None
        if cs.parent_id is not None:
            parent_cs = cs_by_structure_id.get(cs.parent_id)
            if parent_cs is not None:
                parent = restore_or_recreate(parent_cs)
            else:
                # The parent wasn't part of this checkpoint's own section
                # list (shouldn't normally happen, since a checkpoint always
                # snapshots the whole tree) - fall back to whatever's
                # currently live, or leave it a root node if that's gone too.
                parent = Structure.query.filter_by(id=cs.parent_id).first()

        new_structure = Structure(title=cs.title, displayorder=cs.displayorder,
                                  project=checkpoint.project, parent=parent)
        db.session.add(new_structure)
        db.session.add(Section(body=cs.section_body, structure=new_structure))
        db.session.add(SectionSynopsis(body=cs.synopsis_body, structure=new_structure))
        db.session.add(SectionNotes(body=cs.notes_body, structure=new_structure))
        db.session.add(SectionCharacters(body=cs.characters_body, structure=new_structure))
        # Flush so new_structure.id is populated in case a child of this
        # node also needs recreating and has to attach to it as a parent.
        db.session.flush()

        resolved[cs.structure_id] = new_structure
        return new_structure

    for cs in checkpoint.sections:
        restore_or_recreate(cs)

    db.session.commit()
    return jsonify(status=True, status_text=gettext("Restored the checkpoint: '%(label)s'.", label=checkpoint.label))


@bp.route('/get_checkpoints/<int:project_id>', methods=['GET'])
def get_checkpoints(project_id):
    """
    Get the checkpoints for this project.
    """
    # project_id is client-supplied - verify it's owned by this user before returning anything
    get_owned_project_or_404(project_id)
    checkpoints = Checkpoint.query.filter_by(project_id=project_id).order_by(Checkpoint.created_date.desc()).all()
    checkpoints_dict = [checkpoint.to_dict() for checkpoint in checkpoints]
    return jsonify(checkpoints_dict)


@bp.app_errorhandler(CSRFError)
def handle_csrf_error(error):
    return render_template('editor/csrf_error.jinja', reason=error.description), 400
