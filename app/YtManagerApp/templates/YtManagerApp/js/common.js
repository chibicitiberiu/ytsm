function zeroFill(number, width) {
    width -= number.toString().length;
    if ( width > 0 ) {
        return new Array( width + (/\./.test( number ) ? 2 : 1) ).join( '0' ) + number;
    }
    return number + ""; // always return a string
}

function syncNow() {
    $.post("{% url 'ajax_action_sync_now' %}", {
        csrfmiddlewaretoken: '{{ csrf_token }}'
    });
}

function ajaxLink_Clicked() {
    let url_post = $(this).data('post-url');
    let url_get = $(this).data('get-url');

    if (url_post != null) {
        $.post(url_post, {
            csrfmiddlewaretoken: '{{ csrf_token }}'
        });
    }
    else if (url_get != null) {
        $.get(url_get, {
            csrfmiddlewaretoken: '{{ csrf_token }}'
        });
    }
    return false;
}

///
/// Initialization
///
$(document).ready(function ()
{
    $(".ajax-link").on("click", ajaxLink_Clicked);
    $("#btn_sync_now").on("click", syncNow);
});
