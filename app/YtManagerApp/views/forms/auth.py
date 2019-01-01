from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.urls import reverse_lazy


class ExtendedAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(label='Remember me', required=False, initial=False)

    def clean(self):
        remember_me = self.cleaned_data.get('remember_me')
        if remember_me:
            expiry = 3600 * 24 * 30
        else:
            expiry = 0
        self.request.session.set_expiry(expiry)

        return super().clean()


class ExtendedUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False,
                             label='E-mail address',
                             help_text='The e-mail address is optional, but it is the only way to recover a lost '
                                       'password.')
    first_name = forms.CharField(max_length=30, required=False,
                                 label='First name')
    last_name = forms.CharField(max_length=150, required=False,
                                label='Last name')

    form_action = reverse_lazy('register')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_action = self.form_action
        self.helper.add_input(Submit('submit', 'register'))

    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email', 'first_name', 'last_name']
