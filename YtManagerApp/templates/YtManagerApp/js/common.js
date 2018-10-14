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


class AjaxModal
{
    constructor(url)
    {
        this.wrapper = $("#modal-wrapper");
        this.loading = $("#modal-loading");
        this.url = url;
        this.modal = null;
        this.form = null;
        this.submitCallback = null;
    }

    setSubmitCallback(callback) {
        this.submitCallback = callback;
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

        let pThis = this;
        this.form.submit(function(e) {
            pThis._submit(e);
        })
    }

    _loadFailed() {
        this.wrapper.html('<div class="alert alert-danger">An error occurred while displaying the dialog!</div>');
    }

    _submit(e) {
        let pThis = this;
        let url = this.form.attr('action');
        $.post(this.url, this.form.serialize())
            .done(function(result) {
                pThis._submitDone(result);
            })
            .fail(function() {
                pThis._submitFailed();
            });

        e.preventDefault();
    }

    _submitDone(result) {
        // Clear old errors first
        this.form.find('.modal-field-error').remove();

        if (result.success) {
            this._hideModal();
            if (this.submitCallback != null)
                this.submitCallback();
        }
        else {
            for (let field in result.errors)
                if (result.errors.hasOwnProperty(field))
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
