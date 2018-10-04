function onSelectionChanged(e, data)
{
    node = data.instance.get_selected(true)[0];
}

function validateChange(operation, node, parent, position, more)
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

function setupTree(dataIn)
{
    $("#tree-wrapper").jstree({
        core : {
            data : {
                url : 'ajax/get_children'
            },
            check_callback : validateChange,
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
    $("#tree-wrapper").on("changed.jstree", onSelectionChanged);
}

$(document).ready(function () 
{
    setupTree();
})
