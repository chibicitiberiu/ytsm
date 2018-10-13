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