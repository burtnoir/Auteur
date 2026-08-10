document.addEventListener("DOMContentLoaded", (event) => {

    const sectionEditor = new MarkdownEditor('#section_text', {
        'mode': 'hybrid',
        'placeholder': 'Write your markdown...',
        'toolbar': ['heading', 'bold', 'italic', 'strikethrough', 'ul', 'ol', 'checklist', 'blockquote', 'link', 'preview'],
        'onChange': function (value) {
            window.saveText();
        }
    });

    const projectId = $('#tree').data('project-id');
    const projectTree = new mar10.Wunderbaum(
        {
            "element": document.getElementById("tree"),
            "id": "wunderbaum_tree",
            "iconMap": "fontawesome6",
            "source": {
                "url": SCRIPT_ROOT + '/get_project_tree',
                "params": {"project_id": projectId}
            },
            "activate": function (e) {
                // If more than one was selected we just use the first
                // one to get the section text.
                fetch(SCRIPT_ROOT + '/get_section?' + new URLSearchParams({
                    structure_id: e.node.key
                }))
                    .then(response => {
                        if (!response.ok) {
                            console.log('Problem with the get_section: %o', response.json());
                            $('#statusbar').html('Problem with the get_section');
                        }
                        return response.json();
                    })
                    .then(data => {
                        $('#section_id').val(data.section_id);
                        $('#section_text').val(data.section_text);
                        $('#section_children_text').html(data.section_children_text);
                        sectionEditor.render();
                        $('#synopsis_id').val(data.synopsis_id);
                        $('#synopsis_text').val(data.synopsis_text);
                        $('#notes_id').val(data.notes_id);
                        $('#notes_text').val(data.notes_text);
                        $('#character_id').val(data.characters_id);
                        $('#character_text').val(data.characters_text);
                    })
                    .catch(error => console.error('There was an error with the Get Section Fetch operation: ', error));
            },
            "edit": {
                // Controls the node renaming operation.
                "trigger": ["clickActive", "F2"],
                "select": true,
                "apply": function (e) {
                    // Post the data to be saved and notify the user when it's done.
                    fetch(SCRIPT_ROOT + '/update_node', {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                        },
                        body: JSON.stringify({
                            "id": e.node.data.id,
                            "text": e.newValue
                        }, null, '\t')
                    })
                        .then(response => {
                            if (!response.ok) {
                                console.log('Problem with the update_node: %o', response.json());
                                $('#statusbar').html('Problem with the update_node');
                            }
                            return response.json();
                        })
                        .then(data => {
                            $('#statusbar').html(data.status_text);
                        })
                        .catch(error => console.error('There was an error with the Update Node Fetch operation: ', error));
                }
            }
        }
    );


        /**
         * Go to the server, add the new database entry and only then create
         * the new node. This would make sure we have an id for it. Then
         * trigger the edit.
         */
        window.treeAdd = function (project_id) {

            // First get the selected node so we know the parent.
            let ref = projectTree.activeNode;

            if (!ref) {
                return false;
            }

            // Now assemble the data to send to the server.
            const x = {
                "pos": "last",
                "parent": ref.key
            };

            fetch(SCRIPT_ROOT + '/add_node/' + project_id, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: JSON.stringify(x, null, '\t')
            })
                .then(response => {
                    if (!response.ok) {
                        console.log('Problem with the tree add: %o', response.json());
                        $('#statusbar').html('Problem with the tree_add');
                    }
                    return response.json();
                })
                .then(data => {
                    // Now we can create the node because we will have all
                    // the information needed. Id will be passed back from the
                    // server.
                    ref.setExpanded(true);
                    const new_node = ref.addChildren(data.children);

                    // Put the new node into edit mode so the user can enter the title they want.
                    if (new_node) {

                        // The addChildren()/setExpanded() calls above queue a throttled
                        // viewport redraw that lands on the next animation frame and
                        // rebuilds row markup — which wipes out an edit <input> created
                        // before that redraw fires. Defer starting the edit until after
                        // that redraw has run.
                        requestAnimationFrame(() => requestAnimationFrame(() => new_node.startEditTitle()))
                    }
                    $('#statusbar').html(data.status_text);
                })
                .catch(error => console.error('There was an error with the Tree Add Fetch operation: ', error));

        };

        /**
         * Request a delete of the node(s) and the associated text from the server.
         */
        window.treeDelete = function () {
            let ref = projectTree.activeNode;

            if (!ref) {
                return false;
            }

            fetch(SCRIPT_ROOT + '/delete_node', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: JSON.stringify({"id": ref.key}, null, '\t')
            })
                .then(response => {
                    if (!response.ok) {
                        console.log('Problem with the delete_node: %o', response.json());
                        $('#statusbar').html('Problem with the delete_node');
                    }
                    return response.json();
                })
                .then(data => {
                    // Now the server is done we can delete the node(s).
                    ref.remove();
                    $('#statusbar').html(data.status_text);
                    return false;
                })
                .catch(error => console.error('There was an error with the Delete Node Fetch operation: ', error));

        };

        /**
         * Go to the server to update the project information.
         */
        window.editProject = function (project_id) {

            const formData = new FormData($("#editprojectform")[0]);
            fetch(SCRIPT_ROOT + '/update_project/' + project_id, {
                method: "POST",
                headers: {
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: formData
            })
                .then(response => {
                    if (!response.ok) {
                        console.log('Problem with the saveText: %o', response.json());
                        $('#statusbar').html('Problem with the saveText');
                    }
                    return response.json();
                })
                .then(data => {
                    // Now we need to check for errors. If there are any
                    // then they need to be shown.
                    if (data.status) {
                        $('#descriptionerrors, #nameerrors').empty();
                        $('#descriptiongroup, #namegroup').removeClass('has-error');
                        $('#statusbar').html(data.status_text);
                    } else {
                        if (data.name_errors.length > 0) {
                            let errors = '';
                            $('#namegroup').addClass('has-error');
                            for (let error in data.name_errors) {
                                errors += '<li>' + data.name_errors[error] + '</li>';
                            }
                            $('#nameerrors').html(errors);
                        }
                        if (data.description_errors.length > 0) {
                            let errors = '';
                            $('#descriptiongroup').addClass('has-error');
                            for (let error in data.description_errors) {
                                errors += '<li>' + data.description_errors[error] + '</li>';
                            }
                            $('#descriptionerrors').html(errors);
                        }
                    }
                })
                .catch(error => console.error('There was an error with the Save Text Fetch operation: ', error));

        };

        /**
         * Go to the server to save the section text.
         */
        window.saveText = function (value) {

            // Post the data to be saved and notify the user when it's done.
            const formData = new FormData($("#mainform")[0]);
            fetch(SCRIPT_ROOT + '/update_section', {
                method: "POST",
                headers: {
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: formData
            })
                .then(response => {
                    if (!response.ok) {
                        console.log('Problem with the saveText: %o', response.json());
                        $('#statusbar').html('Problem with the saveText');
                    }
                    return response.json();
                })
                .then(data => {
                    $('#statusbar').html(data.status_text);
                })
                .catch(error => console.error('There was an error with the Save Text Fetch operation: ', error));

        };

        /**
         * Go to the server to update the synopsis information.
         */
        window.saveSynopsis = function () {

            // Post the data to be saved and notify the user when it's done.
            const formData = new FormData($("#synopsisform")[0]);
            fetch(SCRIPT_ROOT + '/update_synopsis', {
                method: "POST",
                headers: {
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: formData
            })
                .then(response => {
                    if (!response.ok) {
                        console.log('Problem with the saveSynopsis: %o', response.json());
                        $('#statusbar').html('Problem with the saveSynopsis');
                    }
                    return response.json();
                })
                .then(data => {
                    $('#statusbar').html(data.status_text);
                })
                .catch(error => console.error('There was an error with the Save Synopsis Fetch operation: ', error));

        };

        /**
         * Go to the server to update the synopsis information.
         */
        window.saveNotes = function () {

            // Post the data to be saved and notify the user when it's done.
            const formData = new FormData($("#notesform")[0]);
            fetch(SCRIPT_ROOT + '/update_notes', {
                method: "POST",
                headers: {
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: formData
            })
                .then(response => {
                    if (!response.ok) {
                        console.log('Problem with the saveSynopsis: %o', response.json());
                        $('#statusbar').html('Problem with the saveSynopsis');
                    }
                    return response.json();
                })
                .then(data => {
                    $('#statusbar').html(data.status_text);
                })
                .catch(error => console.error('There was an error with the Save Synopsis Fetch operation: ', error));

        };

        /**
         * Go to the server to update the characters information.
         */
        window.saveCharacters = function () {

            // Post the data to be saved and notify the user when it's done.
            const formData = new FormData($("#characterform")[0]);
            fetch(SCRIPT_ROOT + '/update_characters', {
                method: "POST",
                headers: {
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: formData
            })
                .then(response => {
                    if (!response.ok) {
                        console.log('Problem with the saveCharacters: %o', response.json());
                        $('#statusbar').html('Problem with the saveCharacters');
                    }
                    return response.json();
                })
                .then(data => {
                    $('#statusbar').html(data.status_text);
                })
                .catch(error => console.error('There was an error with the Save Characters Fetch operation: ', error));

        };


        $('#synopsisform :input').change(function () {
            window.saveSynopsis();
        });

        $("#synopsisform").submit(function (event) {
            event.preventDefault();
            window.saveSynopsis();
        });

        $('#notesform :input').change(function () {
            window.saveNotes();
        });

        $("#notesform").submit(function (event) {
            event.preventDefault();
            window.saveNotes();
        });

        $('#characterform :input').change(function () {
            window.saveCharacters();
        });

        $("#characterform").submit(function (event) {
            event.preventDefault();
            window.saveCharacters();
        });

        // Whole-rail collapse toggles
        function wireRailToggle(sidebarId, toggleId, openIcon, closedIcon) {
            const $sidebar = $('#' + sidebarId);
            const $toggle = $('#' + toggleId);
            $toggle.click(function () {
                $sidebar.toggleClass('collapsed');
                const collapsed = $sidebar.hasClass('collapsed');
                $toggle.html(collapsed ? closedIcon : openIcon);
            });
        }

        wireRailToggle('leftsidebar', 'toggleLeft', '<i class="fa-solid fa-chevron-left"></i>', '<i class="fa-solid fa-chevron-right"></i>');
        wireRailToggle('rightsidebar', 'toggleRight', '<i class="fa-solid fa-chevron-right"></i>', '<i class="fa-solid fa-chevron-left"></i>');

        // Attach the export events
        $('.export').on('click', function (event) {
            window.open(SCRIPT_ROOT + '/export_project/' + this.dataset.project_id, '_blank');
            return false;
        });

        $('.export_pdf').on('click', function (event) {
            window.open(SCRIPT_ROOT + '/export_project_pdf/' + this.dataset.project_id, '_blank');
            return false;
        });
    });