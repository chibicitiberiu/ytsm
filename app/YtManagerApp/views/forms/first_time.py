import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Submit, Column
from django import forms
from django.contrib.auth.models import User
from django.urls import reverse_lazy

from YtManagerApp.views.forms.auth import ExtendedUserCreationForm, ExtendedAuthenticationForm

logger = logging.getLogger("FirstTimeWizard")


class WelcomeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit('submit', value='Continue')
        )


class ApiKeyForm(forms.Form):
    api_key = forms.CharField(label="YouTube API Key:")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'api_key',
            Column(
                Submit('submit', value='Continue'),
                HTML('<a href="{% url \'first_time_2\' %}" class="btn btn-secondary">Skip</a>')
            )
        )


class UserCreationForm(ExtendedUserCreationForm):
    form_action = reverse_lazy('first_time_2')


class LoginForm(ExtendedAuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            'remember_me',
            Column(
                Submit('submit', value='Continue'),
                HTML('<a href="{% url \'first_time_2\' %}?register=1" class="btn">Register new admin account</a>')
            )
        )


class PickAdminUserForm(forms.Form):
    admin_user = forms.ModelChoiceField(
            User.objects.order_by('username'),
            label='User to promote to admin',
            required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'admin_user',
            Column(
                Submit('submit', value='Continue'),
                HTML('<a href="{% url \'first_time_2\' %}&register=1" class="btn">Register a new admin user</a>')
            )
        )


class ServerConfigForm(forms.Form):

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


class DoneForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit('submit', value='Finish')
        )
