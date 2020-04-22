export class AjaxModal
{
    wrapper = null;
    loading = null;
    url = "";
    modal = null;
    form = null;
    modalLoadingRing = null;

    submitCallback = null;

    constructor(url) {
        this.wrapper = $("#modal-wrapper");
        this.loading = $("#modal-loading");
        this.url = url;
    }

    _showLoading() {
        this.loading.fadeIn(500);
    }

    _hideLoading() {
        this.loading.fadeOut(100);
    }

    _showModal() {
        if (this.modal != null)
            this.modal.modal();
    }

    _hideModal() {
        if (this.modal != null)
            this.modal.modal('hide');
    }

    _load(result) {
        this.wrapper.html(result);

        this.modal = this.wrapper.find('.modal');
        this.form = this.wrapper.find('form');
        this.modalLoadingRing = this.wrapper.find('#modal-loading-ring');

        let pThis = this;
        this.form.on("submit", function(e) {
            pThis._submit(e);
        });
    }

    _loadFailed() {
        this.wrapper.html('<div class="alert alert-danger">An error occurred while displaying the dialog!</div>');
    }

    _submit(e) {
        let pThis = this;
        let url = this.form.attr('action');
        let ajax_settings = {
            url: url,
        };

        if (this.form.attr('enctype') === 'multipart/form-data') {
            ajax_settings.data = new FormData(this.form[0]);
            ajax_settings.contentType = false;
            ajax_settings.processData = false;
            ajax_settings.cache = false;
        }
        else {
            ajax_settings.data = this.form.serialize();
        }

        $.post(ajax_settings)
            .done(function(result) {
                pThis._submitDone(result);
            })
            .fail(function() {
                pThis._submitFailed();
            })
            .always(function() {
                pThis.modalLoadingRing.fadeOut(100);
                pThis.wrapper.find(":input").prop("disabled", false);
            });

        this.modalLoadingRing.fadeIn(200);
        this.wrapper.find(":input").prop("disabled", true);

        e.preventDefault();
    }

    _submitDone(result) {
        // Clear old errors first
        this.form.find('.modal-field-error').remove();

        if (!result.hasOwnProperty('success')) {
            this._submitInvalidResponse();
            return;
        }

        if (result.success) {
            this._hideModal();
            if (this.submitCallback != null)
                this.submitCallback();
        }
        else {
            if (!result.hasOwnProperty('errors')) {
                this._submitInvalidResponse();
                return;
            }

            for (let field in result.errors)
            {
                let errorsArray = result.errors[field];
                let errorsConcat = "<div class=\"alert alert-danger modal-field-error\"><ul>";

                for(let error of errorsArray) {
                    errorsConcat += `<li>${error.message}</li>`;
                }
                errorsConcat += '</ul></div>';

                if (field === '__all__')
                    this.form.find('.modal-body').append(errorsConcat);
                else
                    this.form.find(`[name='${field}']`).after(errorsConcat);
            }

            let errorsHtml = '';

            let err = this.modal.find('#__modal_error');
            if (err.length) {
                err.html('An error occurred');
            }
            else {
                this.modal.find('.modal-body').append(errorsHtml)
            }
        }
    }

    _submitFailed() {
        // Clear old errors first
        this.form.find('.modal-field-error').remove();
        this.form.find('.modal-body')
            .append(`<div class="alert alert-danger modal-field-error">An error occurred while processing request!</div>`);
    }

    _submitInvalidResponse() {
        // Clear old errors first
        this.form.find('.modal-field-error').remove();
        this.form.find('.modal-body')
            .append(`<div class="alert alert-danger modal-field-error">Invalid server response!</div>`);
    }

    loadAndShow()
    {
        let pThis = this;
        this._showLoading();

        $.get(this.url)
            .done(function (result) {
                pThis._load(result);
                pThis._showModal();
            })
            .fail(function () {
                pThis._loadFailed();
            })
            .always(function() {
                pThis._hideLoading();
            });
    }
}