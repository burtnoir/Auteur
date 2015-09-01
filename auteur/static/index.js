$(document)
	.ready(
		function() {

		    /**
		     * Go to the server to update the project list depending on
		     * whether we are showing the templates or not.
		     */
		    window.templateFilter = function(is_template) {

			// Post the data to be saved and notify the user when
			// it's done.
			$('#projectlist > a')
				.each(
					function(i) {
					    var el = $(this);
					    if ((is_template && el
						    .data('is_template') === 'True')
						    || (!is_template && el
							    .data('is_template') === 'False')) {
						el.show();
					    } else {
						el.hide();
					    }
					});
		    };

		    $('#showTemplates').click(function() {
			templateFilter(true);
		    });

		    $('#showProjects').click(function() {
			templateFilter(false);
		    });

		    $('#showDeletedProjects').click(function() {
			templateFilter(false);
		    });

		    // Initial filter.
		    window.templateFilter(false);
		});