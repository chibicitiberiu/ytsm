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
        filterForm_folderId.val('');
        filterForm_subId.val(id);
    }

    videos_Reload();
}

function videos_Reload()
{
    videos_Submit.call($('#form_video_filter'));
}

let videos_timeout = null;

function videos_ResetPageAndReloadWithTimer()
{
    let filters_form = $("#form_video_filter");
    filters_form.find('input[name=page]').val("1");

    clearTimeout(videos_timeout);
    videos_timeout = setTimeout(function()
    {
        videos_Reload();
        videos_timeout = null;
    }, 200);
}

function videos_PageClicked()
{
    // Obtain page from button
    let page = $(this).data('navigation-page');

    // Set page
    let filters_form = $("#form_video_filter");
    filters_form.find('input[name=page]').val(page);

    // Reload
    videos_Reload();
    $("html, body").animate({ scrollTop: 0 }, "slow");
}

function videos_Submit(e)
{
    let loadingDiv = $('#videos-loading');
    loadingDiv.fadeIn(300);

    let form = $(this);
    let url = form.attr('action');

    $.post(url, form.serialize())
        .done(function(result) {
            $("#videos-wrapper").html(result);
            $(".ajax-link").on("click", ajaxLink_Clicked);
            $(".btn-paging").on("click", videos_PageClicked);
        })
        .fail(function() {
            $("#videos-wrapper").html('<div class="alert alert-danger">An error occurred while retrieving the video list!</div>');
        })
        .always(function() {
            loadingDiv.fadeOut(100);
        });

    if (e != null)
        e.preventDefault();
}

///
/// Notifications
///
const NOTIFICATION_INTERVAL = 1000;

function get_and_process_notifications()
{
    $.get("{% url 'ajax_get_notifications' 12345 %}".replace("12345", LAST_NOTIFICATION_ID))
        .done(function(data) {
            for (let entry of data)
            {
                LAST_NOTIFICATION_ID = entry.id;
                let dt = new Date(entry.time);

                // Status update
                if (entry.msg === 'st-up') {
                    let txt = `<span class="status-timestamp">${dt.getHours()}:${dt.getMinutes()}</span>${entry.status}`;
                    $('#status-message').html(txt);
                }

            }
        });
}

///
/// Initialization
///
$(document).ready(function ()
{
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    tree_Initialize();

    // Subscription toolbar
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
    $("#btn_import").on("click", function () {
        let modal = new AjaxModal("{% url 'modal_import_subscriptions' %}");
        modal.setSubmitCallback(tree_Refresh);
        modal.loadAndShow();
    });
    $("#btn_edit_node").on("click", treeNode_Edit);
    $("#btn_delete_node").on("click", treeNode_Delete);

    // Videos filters
    let filters_form = $("#form_video_filter");
    filters_form.submit(videos_Submit);
    filters_form.find('input[name=query]').on('change', videos_ResetPageAndReloadWithTimer);
    filters_form.find('select[name=sort]').on('change', videos_ResetPageAndReloadWithTimer);
    filters_form.find('select[name=show_watched]').on('change', videos_ResetPageAndReloadWithTimer);
    filters_form.find('select[name=show_downloaded]').on('change', videos_ResetPageAndReloadWithTimer);
    filters_form.find('select[name=results_per_page]').on('change', videos_ResetPageAndReloadWithTimer);

    videos_Reload();

    // Notification manager
    setInterval(get_and_process_notifications, NOTIFICATION_INTERVAL);
});
