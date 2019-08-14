from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import FormView

from YtManagerApp.management.jobs.synchronize import SynchronizeJob
from YtManagerApp.views.forms.settings import SettingsForm, AdminSettingsForm


class SettingsView(LoginRequiredMixin, FormView):
    form_class = SettingsForm
    template_name = 'YtManagerApp/settings.html'
    success_url = reverse_lazy('home')

    def get_initial(self):
        initial = super().get_initial()
        initial.update(SettingsForm.get_initials(self.request.user))
        return initial

    def form_valid(self, form):
        form.save(self.request.user)
        return super().form_valid(form)


class AdminSettingsView(LoginRequiredMixin, FormView):
    form_class = AdminSettingsForm
    template_name = 'YtManagerApp/settings_admin.html'
    success_url = reverse_lazy('home')

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
        initial.update(AdminSettingsForm.get_initials())
        return initial

    def form_valid(self, form):
        form.save()
        SynchronizeJob.schedule_global_job()
        return super().form_valid(form)
