function folderEditDialog_Show(isNew, editNode)
{
    let dialog = $("#folder_edit_dialog");
    dialog.find('#folder_edit_dialog_title').text(isNew ? "New folder" : "Edit folder");
    dialog.find("#folder_edit_dialog_loading").show();
    dialog.find("#folder_edit_dialog_error").hide();
    dialog.find("#folder_edit_dialog_form").hide();
    dialog.modal();

    $.get("{% url 'ajax_get_folders' %}")
        .done(function(folders)
        {
            // Populate list of folders
            let selParent = dialog.find("#folder_edit_dialog_parent");
            selParent.empty();
            selParent.append(new Option('(None)', '#'));

            let parentId = null;
            if (!isNew) {
                parentId = editNode.parent.replace('folder', '');
            }

            for (let folder of folders)
            {
                let o = new Option(folder.text, folder.id);
                if (!isNew && folder.id.toString() === parentId.toString())
                    o.selected = true;

                selParent.append(o);
            }

            // Show form
            dialog.find("#folder_edit_dialog_loading").hide();
            dialog.find("#folder_edit_dialog_form").show();
            dialog.find("#folder_edit_dialog_submit").text(isNew ? "Create" : "Save");

            if (isNew)
            {
                dialog.find("#folder_edit_dialog_id").val('#');
                dialog.find("#folder_edit_dialog_name").val('');
            }
            if (!isNew)
            {
                idTrimmed = editNode.id.replace('folder', '');
                dialog.find("#folder_edit_dialog_id").val(idTrimmed);
                dialog.find("#folder_edit_dialog_name").val(editNode.text);
            }
        })
        .fail(function() {
            let msgError = dialog.find("#folder_edit_dialog_error");
            msgError.show();
            msgError.text("An error occurred!");
        });
}

function folderEditDialog_ShowNew()
{
    folderEditDialog_Show(true, null);
}

function folderEditDialog_Close()
{
    $("#folder_edit_dialog").modal('hide');
}

function folderEditDialog_Submit(e)
{
    let form = $(this);
    let url = form.attr('action');

    $.post(url, form.serialize())
        .done(tree_Refresh);

    folderEditDialog_Close();
    e.preventDefault();
}

function treeNode_Edit()
{
    let selectedNodes = $("#tree-wrapper").jstree('get_selected', true);
    if (selectedNodes.length === 1)
    {
        let node = selectedNodes[0];
        if (node.type === 'folder') {
            folderEditDialog_Show(false, node);
        }
        else {
            // TODO...
        }
    }
}

function treeNode_Delete()
{
    let selectedNodes = $("#tree-wrapper").jstree('get_selected', true);
    if (selectedNodes.length === 1)
    {
        let node = selectedNodes[0];
        if (node.type === 'folder') {
            let folderId = node.id.toString().replace('folder', '');
            if (confirm('Are you sure you want to delete folder "' + node.text + '" and all its descendants?\nNote: the subscriptions won\'t be deleted, they will only be moved outside.'))
            {
                $.post("{% url 'ajax_delete_folder' 99999 %}".replace('99999', folderId), {
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                }).done(tree_Refresh);
            }
        }
        else {
            // TODO...
        }
    }
}

function tree_Initialize()
{
    let treeWrapper = $("#tree-wrapper");
    treeWrapper.jstree({
        core : {
            data : {
                url : "{% url 'ajax_get_children' %}"
            },
            check_callback : tree_ValidateChange,
            themes : {
                dots : false
            },
        },
        types : {
            folder : {
                icon : "material-icons material-folder"
            },
            sub : {
                icon : "material-icons material-person",
                max_depth : 0
            }
        },
        plugins : [ "types", "wholerow", "dnd" ]
    });
    treeWrapper.on("changed.jstree", tree_OnSelectionChanged);
}

function tree_Refresh()
{
    $("#tree-wrapper").jstree("refresh");
}

function tree_ValidateChange(operation, node, parent, position, more)
{
    if (more.dnd)
    {
        // create_node, rename_node, delete_node, move_node and copy_node
        if (operation === "copy_node" || operation === "move_node")
        {
            if (more.ref.type === "sub")
                return false;
        }
    }

    return true;
}

function tree_OnSelectionChanged(e, data)
{
    node = data.instance.get_selected(true)[0];
}

$(document).ready(function () 
{
    tree_Initialize();
    $("#btn_create_folder").on("click", folderEditDialog_ShowNew);
    $("#btn_edit_node").on("click", treeNode_Edit);
    $("#btn_delete_node").on("click", treeNode_Delete);

    $("#folder_edit_dialog_form").submit(folderEditDialog_Submit);
});
