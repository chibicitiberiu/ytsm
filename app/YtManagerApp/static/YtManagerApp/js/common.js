import {JobPanel} from "./components/JobPanel.js";
import {AjaxModal} from "./components/AjaxModal.js";

// Document loaded
jQuery(function() {
    // Setup job panel
    window.ytsm_JobPanel = new JobPanel();
    window.ytsm_JobPanel.enable();

    // Setup hamburger menu
    $('#hamburger-button').on('click', function() {
        $('#hamburger').toggleClass('hamburger-show');
        $('#hamburger-button').toggleClass('hamburger-show');
    });

    // Initialize modals
    $('[data-modal="modal"]').on('click', function() {
        let callbackStr = $(this).data('modal-callback');
        let callback = eval(callbackStr);

        let modal = new AjaxModal($(this).data('modal-url'));
        if (typeof callback === 'function') {
            modal.submitCallback = callback;
        }
        modal.loadAndShow();
    });
});

