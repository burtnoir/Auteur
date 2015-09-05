$(document).ready(
    function () {

        /**
         * Go to the server to update the project information.
         */
        var deleteProject = function (project_id) {

            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + '/delete_project/' + project_id,
                beforeSend: csrfProtect,
                complete: function (data) {

                    var r = data.responseJSON;
                    if (r.status) {
                        // If everythign went well then remove the deleted project from the list.

                        $('#statusbar').html(r.status_text);
                    }
                }
            });
        };


        // Attach a delete event to the project list.
        // TODO: Need to figure out what to do when we are un-deleting.
        $('.deleteProject').on('click', function (event) {
            // Make sure we know which project we are trying to delete.
            // Next step is to make an ajax call to to the deletion.
            console.log(this.dataset.project_id);
            console.log(this.dataset.is_deleted);
            deleteProject(this.dataset.project_id);

            // Need to stop the bubbling or it will do the delete and then go to the project.
            return false;

        });

    });