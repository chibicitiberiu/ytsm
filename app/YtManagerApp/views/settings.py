from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import UpdateView, FormView

from YtManagerApp.management.appconfig import appconfig
from YtManagerApp.models import UserSettings
from YtManagerApp.views.forms.settings import SettingsForm, AdminSettingsForm


class SettingsView(LoginRequiredMixin, UpdateView):
    form_class = SettingsForm
    model = UserSettings
    template_name = 'YtManagerApp/settings.html'
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        obj, _ = self.model.objects.get_or_create(user=self.request.user)
        return obj


class AdminSettingsView(LoginRequiredMixin, FormView):
    form_class = AdminSettingsForm
    template_name = 'YtManagerApp/settings_admin.html'
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseForbidden()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return HttpResponseForbidden()

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: present stats
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial['api_key'] = appconfig.youtube_api_key
        initial['allow_registrations'] = appconfig.allow_registrations
        initial['sync_schedule'] = appconfig.sync_schedule
        initial['scheduler_concurrency'] = appconfig.concurrency
        return initial

    def form_valid(self, form):
        api_key = form.cleaned_data['api_key']
        if api_key is not None and len(api_key) > 0:
            appconfig.youtube_api_key = api_key

        allow_registrations = form.cleaned_data['allow_registrations']
        if allow_registrations is not None:
            appconfig.allow_registrations = allow_registrations

        sync_schedule = form.cleaned_data['sync_schedule']
        if sync_schedule is not None and len(sync_schedule) > 0:
            appconfig.sync_schedule = sync_schedule

        concurrency = form.cleaned_data['scheduler_concurrency']
        if concurrency is not None:
            appconfig.concurrency = concurrency

        return super().form_valid(form)
