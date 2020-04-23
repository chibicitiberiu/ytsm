export class ToastManager {
    toastWrapper = null;

    constructor(toastWrapper) {
        this.toastWrapper = toastWrapper;
    }

    /**
     * Displays a toast message
     * @param caption Title of the toast
     * @param options An object containing the following attributes. Title and message are mandatory:
     *     - body: the main content
     *     - icon: a typcn class which will be used as an icon
     *     - cssClass: additional css classes to apply to the toast (i.e. toast-success, toast-fail)
     *     - duration: duration in milliseconds, defaults to 4000
     */
    toast(caption, options) {
        let body = '';
        if (options.hasOwnProperty('body')) {
            body = `<div class="toast-body">${options.body}</div>`;
        }

        let icon = '';
        if (options.hasOwnProperty('icon')) {
            icon = `<span class="typcn ${options.icon} mr-2"></span>`;
        }

        let cssClass = '';
        if (options.hasOwnProperty('cssClass')) {
            cssClass = options.cssClass;
        }

        let duration = 4000;
        if (options.hasOwnProperty('duration')) {
            duration = options.duration;
        }

        // Generate DOM
        let elem = $(`
            <div class="toast ${cssClass}" role="alert"
                 aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    ${icon}
                    <strong class="mr-auto">${caption}</strong>
                    <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                ${body}
             </div>`);

        elem.appendTo(this.toastWrapper);
        elem.toast({
            animation: true,
            autoHide: true,
            delay: duration
        });
        elem.on('hidden.bs.toast', function () {
            elem.remove();
        });
        elem.toast('show');
    }

    success(caption, options = {}) {
        if (!options.hasOwnProperty('icon')) {
            options.icon = 'typcn-tick';
        }
        if (!options.hasOwnProperty('cssClass')) {
            options.cssClass = 'bg-success'
        }
        this.toast(caption, options);
    }

    warning(caption, options = {}) {
        if (!options.hasOwnProperty('icon')) {
            options.icon = 'typcn-warning';
        }
        if (!options.hasOwnProperty('cssClass')) {
            options.cssClass = 'bg-warning'
        }
        this.toast(caption, options);
    }

    error(caption, options = {}) {
        if (!options.hasOwnProperty('icon')) {
            options.icon = 'typcn-cancel';
        }
        if (!options.hasOwnProperty('cssClass')) {
            options.cssClass = 'bg-danger'
        }
        this.toast(caption, options);
    }
}