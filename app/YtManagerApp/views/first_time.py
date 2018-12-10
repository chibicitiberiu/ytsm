from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Submit
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView, FormView
from django.shortcuts import render, redirect
from YtManagerApp.views.auth import RegisterView
from YtManagerApp.models import UserSettings

from YtManagerApp.management.appconfig import global_prefs
from django.http import HttpResponseForbidden


class ProtectInitializedMixin(object):

    def get(self, request, *args, **kwargs):
        if global_prefs['hidden__initialized']:
            return redirect('home')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if global_prefs['hidden__initialized']:
            return HttpResponseForbidden()
        return super().post(request, *args, **kwargs)


#
# Step 0: welcome screen
#
class Step0WelcomeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit('submit', value='Continue')
        )


class Step0WelcomeView(ProtectInitializedMixin, FormView):
    template_name = 'YtManagerApp/first_time_setup/step0_welcome.html'
    form_class = Step0WelcomeForm
    success_url = reverse_lazy('first_time_1')


#
# Step 1: setup API key
#
class Step1ApiKeyForm(forms.Form):
    api_key = forms.CharField(label="YouTube API Key:")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'api_key',
            Submit('submit', value='Continue'),
        )


class Step1ApiKeyView(ProtectInitializedMixin, FormView):
    template_name = 'YtManagerApp/first_time_setup/step1_apikey.html'
    form_class = Step1ApiKeyForm
    success_url = reverse_lazy('first_time_2')

    def form_valid(self, form):
        key = form.cleaned_data['api_key']
        # TODO: validate key
        if key is not None and len(key) > 0:
            global_prefs['general__youtube_api_key'] = key


#
# Step 2: create admin user
#
class Step2CreateAdminUserView(ProtectInitializedMixin, RegisterView):
    template_name = 'YtManagerApp/first_time_setup/step2_admin.html'
    success_url = reverse_lazy('first_time_3')


#
# Step 3: configure server
#
class Step3ConfigureForm(forms.Form):

    allow_registrations = forms.BooleanField(
        label="Allow user registrations",
        help_text="Disabling this option will prevent anyone from registering to the site.",
        initial=True,
        required=False
    )

    sync_schedule = forms.CharField(
        label="Synchronization schedule",
        help_text="How often should the application look for new videos.",
        initial="5 * * * *",
        required=True
    )

    auto_download = forms.BooleanField(
        label="Download videos automatically",
        required=False
    )

    download_location = forms.CharField(
        label="Download location",
        help_text="Location on the server where videos are downloaded.",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h3>Server settings</h3>'),
            'sync_schedule',
            'allow_registrations',
            HTML('<h3>User settings</h3>'),
            'auto_download',
            'download_location',
            Submit('submit', value='Continue'),
        )


class Step3ConfigureView(ProtectInitializedMixin, FormView):
    template_name = 'YtManagerApp/first_time_setup/step3_configure.html'
    form_class = Step3ConfigureForm
    success_url = reverse_lazy('first_time_done')

    def form_valid(self, form):
        allow_registrations = form.cleaned_data['allow_registrations']
        if allow_registrations is not None:
            global_prefs['general__allow_registrations'] = allow_registrations

        sync_schedule = form.cleaned_data['sync_schedule']
        if sync_schedule is not None and len(sync_schedule) > 0:
            global_prefs['scheduler__synchronization_schedule'] = sync_schedule

        auto_download = form.cleaned_data['auto_download']
        if auto_download is not None:
            self.request.user.preferences['downloader__auto_enabled'] = auto_download

        download_location = form.cleaned_data['download_location']
        if download_location is not None and len(download_location) > 0:
            self.request.user.preferences['downloader__download_path'] = download_location

        # Set initialized to true
        global_prefs['hidden__initialized'] = True
        
        return super().form_valid(form)

#
# Done screen
#
class DoneForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit('submit', value='Finish')
        )


class DoneView(FormView):
    template_name = 'YtManagerApp/first_time_setup/done.html'
    form_class = DoneForm
    success_url = reverse_lazy('home')
