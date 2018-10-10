class Dialog {
    constructor(modalId) {
        this.modal = $(modalId);
        this.title = $(modalId + "_Title");
        this.form = $(modalId + "_Form");
        this.error = $(modalId + "_Error");
        this.loading = $(modalId + "_Loading");
        this.btnSubmit = $(modalId + "_Submit");
        this.setState('normal');
    }

    setTitle(value) {
        this.title.text(value);
    }

    setState(state) {
        if (state === 'loading') {
            this.loading.show();
            this.error.hide();
            this.form.hide();
        }
        if (state === 'error') {
            this.loading.hide();
            this.error.show();
            this.form.hide();
        }
        if (state === 'normal') {
            this.loading.hide();
            this.error.hide();
            this.form.show();
        }
    }

    setError(text) {
        this.error.text(text);
    }

    showModal() {
        this.modal.modal();
    }

    hideModal() {
        this.modal.modal('hide');
    }
}

class FolderEditDialog extends Dialog {

    constructor (modalId) {
        super(modalId);
        this.field_Id = $(modalId + "_Id");
        this.field_Name = $(modalId + "_Name");
        this.field_Parent = $(modalId + "_Parent");

        let pThis = this;
        this.form.submit(function(e) {
            pThis.submit(e);
        })
    }

    setParentFolderOptions(folders, selectedId)
    {
        // Populate list of folders
        this.field_Parent.empty();
        this.field_Parent.append(new Option('(None)', '#'));

        for (let folder of folders)
        {
            let o = new Option(folder.text, folder.id);
            if (selectedId != null && folder.id.toString() === selectedId.toString())
                o.selected = true;

            this.field_Parent.append(o);
        }
    }

    show (isNew, editNode) {
        let pThis = this;
        this.setTitle(isNew ? "New folder" : "Edit folder");
        this.setState('loading');
        this.showModal();

        $.get("{% url 'ajax_get_folders' %}")
            .done(function(folders)
            {
                let parentId = null;
                if (!isNew) {
                    parentId = editNode.parent.replace('folder', '');
                }

                pThis.setParentFolderOptions(folders, parentId);
                pThis.setState('normal');
                pThis.btnSubmit.text(isNew ? "Create" : "Save");

                if (isNew)
                {
                    pThis.field_Id.val('#');
                    pThis.field_Name.val('');
                }
                if (!isNew)
                {
                    let idTrimmed = editNode.id.replace('folder', '');
                    pThis.field_Id.val(idTrimmed);
                    pThis.field_Name.val(editNode.text);
                }
            })
            .fail(function() {
                pThis.setState('error');
                pThis.setError('An error occurred!');
            });
    }

    showNew() {
        this.show(true, null);
    }

    showEdit(editNode) {
        this.show(false, editNode);
    }

    submit(e) {
        let url = this.form.attr('action');

        $.post(url, this.form.serialize())
            .done(tree_Refresh);

        this.hideModal();
        e.preventDefault();
    }
}

class SubscriptionEditDialog extends Dialog {

    constructor (modalId) {
        super(modalId);
        this.field_Id = $(modalId + "_Id");
        this.field_Url = $(modalId + "_Url");
        this.field_Name = $(modalId + "_Name");
        this.field_Parent = $(modalId + "_Parent");

        let pThis = this;
        this.form.submit(function(e) {
            pThis.submit(e);
        })
    }

    setParentFolderOptions(folders, selectedId)
    {
        // Populate list of folders
        this.field_Parent.empty();
        this.field_Parent.append(new Option('(None)', '#'));

        for (let folder of folders)
        {
            let o = new Option(folder.text, folder.id);
            if (selectedId != null && folder.id.toString() === selectedId.toString())
                o.selected = true;

            this.field_Parent.append(o);
        }
    }

    show (isNew, editNode) {
        let pThis = this;
        this.setTitle(isNew ? "New subscription" : "Edit subscription");
        this.setState('loading');
        this.showModal();

        $.get("{% url 'ajax_get_folders' %}")
            .done(function(folders)
            {
                let parentId = null;
                if (!isNew) {
                    parentId = editNode.parent.replace('folder', '');
                }

                pThis.setParentFolderOptions(folders, parentId);
                pThis.setState('normal');
                pThis.btnSubmit.text(isNew ? "Create" : "Save");

                if (isNew)
                {
                    pThis.field_Id.val('#');
                    pThis.field_Url.show();
                    pThis.field_Url.val('');
                    pThis.field_Name.hide();
                    pThis.field_Name.val('');
                }
                if (!isNew)
                {
                    let idTrimmed = editNode.id.replace('sub', '');
                    pThis.field_Id.val(idTrimmed);
                    pThis.field_Url.hide();
                    pThis.field_Url.val('');
                    pThis.field_Name.show();
                    pThis.field_Name.val(editNode.text);
                }
            })
            .fail(function() {
                pThis.setState('error');
                pThis.setError('An error occurred!');
            });
    }

    showNew() {
        this.show(true, null);
    }

    showEdit(editNode) {
        this.show(false, editNode);
    }

    submit(e) {
        let url = this.form.attr('action');

        $.post(url, this.form.serialize())
            .done(tree_Refresh);

        this.hideModal();
        e.preventDefault();
    }
}


function treeNode_Edit()
{
    let selectedNodes = $("#tree-wrapper").jstree('get_selected', true);
    if (selectedNodes.length === 1)
    {
        let node = selectedNodes[0];
        if (node.type === 'folder') {
            folderEditDialog.showEdit(node);
        }
        else {
            subscriptionEditDialog.showEdit(node);
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
            let subId = node.id.toString().replace('sub', '');
            if (confirm('Are you sure you want to delete subscription "' + node.text + '"?'))
            {
                $.post("{% url 'ajax_delete_subscription' 99999 %}".replace('99999', subId), {
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                }).done(tree_Refresh);
            }
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
                icon : "typcn typcn-folder"
            },
            sub : {
                icon : "typcn typcn-user",
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
    $.post("{% url 'ajax_list_videos' %}", {
        type: node.type,
        id: node.id.replace('folder', '').replace('sub', ''),
        csrfmiddlewaretoken: '{{ csrf_token }}'
    }).done(function (result) {
        $("#main_detail").html(result);
    });
}

///
/// Globals
///
let folderEditDialog = null;
let subscriptionEditDialog = null;

///
/// Initialization
///
$(document).ready(function ()
{
    tree_Initialize();

    folderEditDialog = new FolderEditDialog('#folderEditDialog');
    subscriptionEditDialog = new SubscriptionEditDialog('#subscriptionEditDialog');

    $("#btn_create_sub").on("click", function () { subscriptionEditDialog.showNew(); });
    $("#btn_create_folder").on("click", function () { folderEditDialog.showNew(); });
    $("#btn_edit_node").on("click", treeNode_Edit);
    $("#btn_delete_node").on("click", treeNode_Delete);
});
