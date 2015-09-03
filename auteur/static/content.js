$(document).ready(
    function () {

        csrfProtect = function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                var csrftoken = $('meta[name=csrf-token]').attr('content');
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        };

        var resizer = function (ed) {
            var h = $('body').height(),
                t = $('#topnav').height(),
                b = $('#bottombar').height();
            ed.resize('100%', h - t - b);
        };

        // Replace the textarea with a CKEditor
        // instance, using default configuration.
        CKEDITOR.replace('sectiontext', {
            on: {
                instanceReady: function (ev) {
                    resizer(ev.editor);
                }
            }
        });

        $(window).resize(function () {
            resizer(CKEDITOR.instances.sectiontext);
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
                $.getJSON(SCRIPT_ROOT + '/get_section', {
                    structure_id: data.instance
                        .get_node(data.selected[0]).id
                }, function (data) {
                    $('#section_id').val(data.section_id);
                    CKEDITOR.instances.sectiontext.setData(data.section_text);
                    $('#synopsis_id').val(data.synopsis_id);
                    $('#synopsis_text').val(data.synopsis_text);
                    $('#notes_id').val(data.notes_id);
                    $('#notes_text').val(data.notes_text);
                });
            }).on('rename_node.jstree', function (evt, data) {

            // Assemble the data and send it to the server.
            var x = {
                "id": data.node.id,
                "text": data.text
            };

            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + '/update_node',
                data: JSON.stringify(x, null, '\t'),
                beforeSend: csrfProtect,
                contentType: 'application/json;charset=UTF-8',
                done: function (data) {
                    $('#statusbar').html(data.responseJSON.status_text);
                }
            });
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
            var ref = $('#tree').jstree(true),
                sel = ref.get_selected();
            if (!sel.length) {
                return false;
            }
            sel = sel[0];

            // Now assemble the data to send to the server.
            var x = {
                "pos": "last",
                "parent": sel
            };

            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + '/add_node/' + project_id,
                data: JSON.stringify(x, null, '\t'),
                beforeSend: csrfProtect,
                contentType: 'application/json;charset=UTF-8',
                complete: function (data) {

                    // Now we can create the node because we will have all
                    // the
                    // information needed. Id will be passed back from the
                    // server.
                    var responseJSON = data.responseJSON,
                        new_node = ref.create_node(sel, {
                            "text": responseJSON.text,
                            "type": "file",
                            "data": {
                                "treeid": responseJSON.id,
                                "displayorder": responseJSON.displayorder
                            }
                        }, x.pos, function (n) {
                            $('#tree').jstree(true).set_id(n.id,
                                responseJSON.id);
                        });

                    if (new_node) {
                        ref.edit(new_node);
                    }
                    $('#statusbar').html(responseJSON.status_text);
                }
            });

        };

        /**
         * Find out which node has been selected and switch it to edit mode.
         */
        window.treeRename = function () {
            var ref = $('#tree').jstree(true),
                sel = ref.get_selected();
            if (!sel.length) {
                return false;
            }
            sel = sel[0];
            ref.edit(sel);
        };

        /**
         *
         */
        window.treeDelete = function () {
            var ref = $('#tree').jstree(true),
                sel = ref.get_selected();
            if (!sel.length) {
                return false;
            }

            // Request a delete of the node(s) and the associated text from
            // the server.
            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + '/delete_node',
                data: JSON.stringify({
                    "ids": sel
                }, null, '\t'),
                beforeSend: csrfProtect,
                contentType: 'application/json;charset=UTF-8',
                complete: function (data) {
                    // Now the server is done we can delete the node(s).
                    ref.delete_node(sel);
                    $('#statusbar').html(data.responseJSON.status_text);
                    return false;
                }
            });
        };

        /**
         * Go to the server to update the project information.
         */
        window.editProject = function (project_id) {

            var errors = '',
                error;

            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + '/update_project/' + project_id,
                data: $("#editprojectform").serialize(),
                beforeSend: csrfProtect,
                complete: function (data) {

                    // Now we need to check for errors. If there are any
                    // then they need to
                    // be shown.
                    var r = data.responseJSON;
                    if (r.status) {
                        $('#descriptionerrors, #nameerrors').empty();
                        $('#descriptiongroup, #namegroup').removeClass('has-error');
                        $('#statusbar').html(r.status_text);
                    } else {
                        errors = '';
                        if (r.name_errors.length > 0) {
                            $('#namegroup').addClass('has-error');
                            for (error in r.name_errors) {
                                errors += '<li>' + r.name_errors[error] + '</li>';
                            }
                            $('#nameerrors').html(errors);
                        }
                        errors = '';
                        if (r.description_errors.length > 0) {
                            $('#descriptiongroup').addClass('has-error');
                            for (error in r.description_errors) {
                                errors += '<li>' + r.description_errors[error] + '</li>';
                            }
                            $('#descriptionerrors').html(errors);
                        }
                    }
                }
            });
        };

        /**
         * Go to the server to update the project information.
         */
        window.saveText = function () {

            // Update the editor before submitting so we get the data sent.
            for (var instance in CKEDITOR.instances) {
                CKEDITOR.instances[instance].updateElement();
            }

            // Post the data to be saved and notify the user when it's done.
            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + '/update_section',
                data: $("#mainform").serialize(),
                beforeSend: csrfProtect,
                complete: function (data) {
                    // Show the response text.
                    $('#statusbar').html(data.responseJSON.status_text);
                }
            });
        };

        /**
         * Go to the server to update the synopsis information.
         */
        window.saveSynopsis = function () {

            // Post the data to be saved and notify the user when it's done.
            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + '/update_synopsis',
                data: $("#synopsisform").serialize(),
                beforeSend: csrfProtect,
                complete: function (data) {
                    // Show the response text.
                    $('#statusbar').html(data.responseJSON.status_text);
                }
            });
        };

        /**
         * Go to the server to update the synopsis information.
         */
        window.saveNotes = function () {

            // Post the data to be saved and notify the user when it's done.
            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + '/update_notes',
                data: $("#notesform").serialize(),
                beforeSend: csrfProtect,
                complete: function (data) {
                    // Show the response text.
                    $('#statusbar').html(data.responseJSON.status_text);
                }
            });
        };

    });