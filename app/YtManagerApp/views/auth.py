from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from YtManagerApp.management.appconfig import appconfig
from YtManagerApp.views.forms.auth import ExtendedAuthenticationForm, ExtendedUserCreationForm


class ExtendedLoginView(LoginView):
    form_class = ExtendedAuthenticationForm


class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = ExtendedUserCreationForm
    success_url = reverse_lazy('register_done')

    def form_valid(self, form):
        form.apply_session_expiry(self.request)
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

    def post(self, request, *args, **kwargs):
        if not appconfig.allow_registrations:
            return HttpResponseForbidden("Registrations are disabled!")

        return super().post(request, *args, **kwargs)


class RegisterDoneView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/register_done.html'
