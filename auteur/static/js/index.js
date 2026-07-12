$(document).ready(
    function () {

        const deleteProjectHelper = function (project_id, endpoint, parent) {

            fetch(SCRIPT_ROOT + endpoint + project_id, {
                method: "POST",
                headers: {
                    "X-CSRFToken": $('meta[name=csrf-token]').attr('content')
                }
            })
                .then(response => {
                    if (!response.ok) {
                        $('#statusbar').html('Problem with the delete project function.');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status) {
                        // If everything went well then remove the deleted project from the list.
                        parent.hide();
                        $('#statusbar').html(data.status_text);
                    }
                })
                .catch(error => console.error('There was an error with the Delete Project Fetch operation: ', error));

        };

        /**
         * Go to the server to update the project information.
         */
        const deleteProject = function (project_id, parent) {
            deleteProjectHelper(project_id, '/delete_project/', parent);
        };

        const undeleteProject = function (project_id, parent) {
            deleteProjectHelper(project_id, '/undelete_project/', parent);
        };


        // Attach a delete event to the project list.
        $('.deleteProject').on('click', function (event) {
            // Next step is to make an ajax call to to the deletion or undeletion.
            if(this.dataset.is_deleted === 'False'){
                deleteProject(this.dataset.project_id, $(this).parent());
            } else {
                undeleteProject(this.dataset.project_id, $(this).parent());
            }

            // Need to stop the bubbling or it will do the delete and then go to the project.
            return false;
        });
    });