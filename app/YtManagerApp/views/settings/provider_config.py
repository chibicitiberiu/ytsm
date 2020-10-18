from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.views.generic import FormView

from YtManagerApp.providers.video_provider import VideoProvider, ProviderValidationError
from YtManagerApp.services import Services
from YtManagerApp.views.controls.modal import ModalMixin


class ProviderConfigForm(forms.Form):

    def __init__(self, *args, **kwargs):

        self.provider_id = kwargs.pop('provider_id', None)
        super().__init__(*args, **kwargs)

        if self.provider_id is not None:
            provider: VideoProvider = Services.videoProviderManager().get(self.provider_id)
            for key, field in provider.settings.items():
                self.fields[key] = field

    def clean(self):
        cleaned_data = super().clean()
        provider: VideoProvider = Services.videoProviderManager().get(self.provider_id)

        try:
            provider.validate_configuration(cleaned_data)
        except ProviderValidationError as ex:
            raise ValidationError(ex.field_messages)


class ProviderConfigView(LoginRequiredMixin, ModalMixin, FormView):
    template_name = 'YtManagerApp/controls/provider_config_modal.html'
    form_class = ProviderConfigForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['provider_id'] = self.kwargs['provider_id']
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['provider'] = Services.videoProviderManager().get(self.kwargs['provider_id'])
        return data

    def get_initial(self):
        initial = super().get_initial()
        cfg = Services.videoProviderManager().get_provider_config(self.kwargs['provider_id'])
        if cfg is not None:
            initial.update(cfg)

    def form_valid(self, form):
        try:
            Services.videoProviderManager().configure_provider(self.kwargs['provider_id'], form.cleaned_data)
        except Exception as ex:
            super().modal_response(form, success=False, error_msg='Configuration of provider failed! ' + str(ex))

        return super().form_valid(form)
