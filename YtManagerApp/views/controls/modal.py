from django.views.generic import TemplateView


class ModalView(TemplateView):
    template_name = 'YtManagerApp/controls/modal.html'

    def __init__(self, modal_id='dialog', title='', fade=True, centered=True, small=False, large=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = modal_id
        self.title = title
        self.fade = fade
        self.centered = centered
        self.small = small
        self.large = large

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['modal_id'] = self.id

        data['modal_classes'] = ''
        if self.fade:
            data['modal_classes'] += 'fade '

        data['modal_dialog_classes'] = ''
        if self.centered:
            data['modal_dialog_classes'] += 'modal-dialog-centered '
        if self.small:
            data['modal_dialog_classes'] += 'modal-sm '
        elif self.large:
            data['modal_dialog_classes'] += 'modal-lg '

        data['modal_title'] = self.title

        return data
