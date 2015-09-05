$(document).ready(
    function () {

        var deleteProjectHelper = function(project_id, endpoint, parent){
            $.ajax({
                type: "POST",
                url: SCRIPT_ROOT + endpoint + project_id,
                beforeSend: csrfProtect,
                complete: function (data) {

                    var r = data.responseJSON;
                    if (r.status) {
                        // If everything went well then remove the deleted project from the list.
                        parent.hide();
                        $('#statusbar').html(r.status_text);
                    }
                }
            });            
        };
        
        /**
         * Go to the server to update the project information.
         */
        var deleteProject = function (project_id, parent) {
            deleteProjectHelper(project_id, '/delete_project/', parent);
        };
        
        var undeleteProject = function (project_id, parent) {
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