$(document).ready(function() {

  // Replace the textarea with a CKEditor
  // instance, using default configuration.
  CKEDITOR.replace('sectiontext');

  // Set up the tree. Needs an array of JSON objects.
  $('#tree').on('changed.jstree', function(e, data) {
    // Nothing to do for a deleted node as it has gone away and taken the text
    // with it.
    if (data.action === 'rename_node' || data.action === 'delete_node')
      return true;
    // If more than one was selected we just use the first one to get the
    // section text.
    $.getJSON(SCRIPT_ROOT + '/get_section', {
      structure_id : data.instance.get_node(data.selected[0]).id
    }, function(data) {
      $('#section_id').val(data.section_id);
      CKEDITOR.instances.sectiontext.setData(data.section_text);
    });
  }).on('rename_node.jstree', function(evt, data) {

    // Assemble the data and send it to the server.
    var x = {
      "id" : data.node.id,
      "text" : data.text
    };

    $.ajax({
      type : "POST",
      url : SCRIPT_ROOT + '/update_node',
      data : JSON.stringify(x, null, '\t'),
      contentType : 'application/json;charset=UTF-8',
    });
  }).jstree({
    'core' : {
      "check_callback" : true,
      'data' : treeData
    }
  });

  /**
   * Go to the server, add the new database entry and only then create the new
   * node. This would make sure we have an id for it. Then trigger the edit.
   */
  window.treeAdd = function(project_id) {

    // First get the selected node so we know the parent.
    var ref = $('#tree').jstree(true);
    var sel = ref.get_selected();
    if (!sel.length) {
      return false;
    }
    sel = sel[0];

    // Now assemble the data to send to the server.
    var x = {
      "pos" : "last",
      "parent" : sel
    };

    $.ajax({
      type : "POST",
      url : SCRIPT_ROOT + '/add_node/' + project_id,
      data : JSON.stringify(x, null, '\t'),
      contentType : 'application/json;charset=UTF-8',
      complete : function(data) {

        // Now we can create the node because we will have all the
        // information needed. Id will be passed back from the server.
        var responseJSON = data.responseJSON;
        var new_node = ref.create_node(sel, {
          "text" : responseJSON.text,
          "type" : "file",
          "data" : {
            "treeid" : responseJSON.id,
            "displayorder" : responseJSON.displayorder
          }
        }, x.pos, function(n) {
          $('#tree').jstree(true).set_id(n.id, responseJSON.id);
        });

        if (new_node) {
          ref.edit(new_node);
        }
      }
    });

  };

  /**
   * Find out which node has been selected and switch it to edit mode.
   */
  window.treeRename = function() {
    var ref = $('#tree').jstree(true), sel = ref.get_selected();
    if (!sel.length) {
      return false;
    }
    sel = sel[0];
    ref.edit(sel);
  };

  /**
   * 
   */
  window.treeDelete = function() {
    var ref = $('#tree').jstree(true);
    var sel = ref.get_selected();
    if (!sel.length) {
      return false;
    }

    // Request a delete of the node(s) and the associated text from the server.
    $.ajax({
      type : "POST",
      url : SCRIPT_ROOT + '/delete_node',
      data : JSON.stringify({
        "ids" : sel
      }, null, '\t'),
      contentType : 'application/json;charset=UTF-8',
      complete : function(data) {
        // Now the server is done we can delete the node(s).
        ref.delete_node(sel);
        return false;
      }
    });
  };

});