$(document).ready(
    function () {

        // const resizer = function (ed) {
        //     const h = $('#body-container').height();
        //     ed.resize('100%', h);
        // };

        // $(window).resize(function () {
        //     resizer(CKEDITOR.instances.sectiontext);
        // });

        const sectionEditor = new MarkdownEditor('#section_text', {
            'mode': 'hybrid',
            'placeholder': 'Write your markdown...',
            'toolbar': ['heading', 'bold', 'italic', 'strikethrough', 'ul', 'ol', 'checklist', 'blockquote', 'link', 'preview'],
            'onChange':function(value) {
                window.saveText();
            }
        });


        // Set up the tree. Needs an array of JSON objects.
        $('#tree').on('changed.jstree',
            function (e, data) {
                // Nothing to do for a deleted node as it has gone away
                // and taken the text with it.
                if (data.action === 'rename_node' || data.action === 'delete_node') {
                    return true;
                }
                // If more than one was selected we just use the first
                // one to get the section text.
                fetch(SCRIPT_ROOT + '/get_section?' + new URLSearchParams({
                    structure_id: data.instance.get_node(data.selected[0]).id
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

            }).on('rename_node.jstree', function (evt, data) {
            // Post the data to be saved and notify the user when it's done.
            fetch(SCRIPT_ROOT + '/update_node', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: JSON.stringify({
                    "id": data.node.id,
                    "text": data.text
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

        }).jstree({
            'core': {
                "check_callback": true,
                'data': treeData
            }
        });

        /**
         * Go to the server, add the new database entry and only then create
         * the new node. This would make sure we have an id for it. Then
         * trigger the edit.
         */
        window.treeAdd = function (project_id) {

            // First get the selected node so we know the parent.
            let ref = $('#tree').jstree(true),
                sel = ref.get_selected();
            if (!sel.length) {
                return false;
            }
            sel = sel[0];

            // Now assemble the data to send to the server.
            const x = {
                "pos": "last",
                "parent": sel
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
                    const new_node = ref.create_node(sel, {
                        "text": responseJSON.text,
                        "type": "file",
                        "data": {
                            "treeid": data.id,
                            "displayorder": data.displayorder
                        }
                    }, x.pos, function (n) {
                        $('#tree').jstree(true).set_id(n.id,
                            data.id);
                    });

                    if (new_node) {
                        ref.edit(new_node);
                    }
                    $('#statusbar').html(data.status_text);
                })
                .catch(error => console.error('There was an error with the Tree Add Fetch operation: ', error));

        };

        /**
         * Find out which node has been selected and switch it to edit mode.
         */
        window.treeRename = function () {
            let ref = $('#tree').jstree(true),
                sel = ref.get_selected();
            if (!sel.length) {
                return false;
            }
            sel = sel[0];
            ref.edit(sel);
        };

        /**
         * Request a delete of the node(s) and the associated text from the server.
         */
        window.treeDelete = function () {
            const ref = $('#tree').jstree(true),
                sel = ref.get_selected();
            if (!sel.length) {
                return false;
            }

            fetch(SCRIPT_ROOT + '/delete_node', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                },
                body: JSON.stringify({"ids": sel}, null, '\t')
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
                    ref.delete_node(sel);
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
    });