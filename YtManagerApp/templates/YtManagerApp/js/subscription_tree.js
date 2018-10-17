class Dialog_old {
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

class FolderEditDialog extends Dialog_old {

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

class SubscriptionEditDialog extends Dialog_old {

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
            let id = node.id.replace('folder', '');
            let modal = new AjaxModal("{% url 'modal_update_folder' 98765 %}".replace('98765', id));
            modal.setSubmitCallback(tree_Refresh);
            modal.loadAndShow();
        }
        else {
            let id = node.id.replace('sub', '');
            let modal = new AjaxModal("{% url 'modal_update_subscription' 98765 %}".replace('98765', id));
            modal.setSubmitCallback(tree_Refresh);
            modal.loadAndShow();
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
            let id = node.id.replace('folder', '');
            let modal = new AjaxModal("{% url 'modal_delete_folder' 98765 %}".replace('98765', id));
            modal.setSubmitCallback(tree_Refresh);
            modal.loadAndShow();
        }
        else {
            let id = node.id.replace('sub', '');
            let modal = new AjaxModal("{% url 'modal_delete_subscription' 98765 %}".replace('98765', id));
            modal.setSubmitCallback(tree_Refresh);
            modal.loadAndShow();
        }
    }
}

function tree_Initialize()
{
    let treeWrapper = $("#tree-wrapper");
    treeWrapper.jstree({
        core : {
            data : {
                url : "{% url 'ajax_get_tree' %}"
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
    let filterForm = $('#form_video_filter');
    let filterForm_folderId = filterForm.find('#form_video_filter_folder_id');
    let filterForm_subId = filterForm.find('#form_video_filter_subscription_id');

    let node = data.instance.get_selected(true)[0];

    // Fill folder/sub fields
    if (node == null) {
        filterForm_folderId.val('');
        filterForm_subId.val('');
    }
    else if (node.type === 'folder') {
        let id = node.id.replace('folder', '');
        filterForm_folderId.val(id);
        filterForm_subId.val('');
    }
    else {
        let id = node.id.replace('sub', '');
        filterForm_folderId.val();
        filterForm_subId.val(id);
    }

    videos_Reload();
}


function videos_Reload()
{
    let filterForm = $('#form_video_filter');
    let loadingDiv = $('#videos-loading');
    loadingDiv.fadeIn(300);

    // Perform query
    $.post("{% url 'ajax_get_videos' %}", filterForm.serialize())
        .done(function (result) {
            $("#videos-wrapper").html(result);
        })
        .fail(function () {
            $("#videos-wrapper").html('<div class="alert alert-danger">An error occurred while retrieving the video list!</div>');
        })
        .always(function() {
            loadingDiv.fadeOut(100);
        });
}


let videos_timeout = null;

function videos_ReloadWithTimer()
{
    clearTimeout(videos_timeout);
    videos_timeout = setTimeout(function()
    {
        videos_Reload();
        videos_timeout = null;
    }, 500);
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

    // folderEditDialog = new FolderEditDialog('#folderEditDialog');
    // subscriptionEditDialog = new SubscriptionEditDialog('#subscriptionEditDialog');
    //
    $("#btn_create_sub").on("click", function () {
        let modal = new AjaxModal("{% url 'modal_create_subscription' %}");
        modal.setSubmitCallback(tree_Refresh);
        modal.loadAndShow();
    });
    $("#btn_create_folder").on("click", function () {
        let modal = new AjaxModal("{% url 'modal_create_folder' %}");
        modal.setSubmitCallback(tree_Refresh);
        modal.loadAndShow();
    });

    // $("#btn_create_folder").on("click", function () { folderEditDialog.showNew(); });
    $("#btn_edit_node").on("click", treeNode_Edit);
    $("#btn_delete_node").on("click", treeNode_Delete);
});
