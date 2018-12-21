from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView


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


class ExtendedLoginView(LoginView):
    form_class = ExtendedAuthenticationForm


class ExtendedUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False,
                             label='E-mail address',
                             help_text='The e-mail address is optional, but it is the only way to recover a lost '
                                       'password.')
    first_name = forms.CharField(max_length=30, required=False,
                                 label='First name')
    last_name = forms.CharField(max_length=150, required=False,
                                label='Last name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse_lazy('register')
        self.helper.add_input(Submit('submit', 'register'))

    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email', 'first_name', 'last_name']


class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = ExtendedUserCreationForm
    success_url = reverse_lazy('register_done')

    def form_valid(self, form):

        form.save()

        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_first_user'] = (User.objects.count() == 0)
        return context


class RegisterDoneView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/register_done.html'
