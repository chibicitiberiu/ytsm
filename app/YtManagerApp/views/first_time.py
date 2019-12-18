import logging

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from YtManagerApp.services.scheduler.jobs.synchronize_job import SynchronizeJob
from YtManagerApp.services import Services
from YtManagerApp.views.forms.first_time import WelcomeForm, ApiKeyForm, PickAdminUserForm, ServerConfigForm, DoneForm, \
    UserCreationForm, LoginForm

logger = logging.getLogger("FirstTimeWizard")


class WizardStepMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):

        # Prevent access if application is already initialized
        if Services.appConfig().initialized:
            logger.debug(f"Attempted to access {request.path}, but first time setup already run. Redirected to home "
                         f"page.")
            return redirect('home')

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if Services.appConfig().initialized:
            logger.debug(f"Attempted to post {request.path}, but first time setup already run.")
            return HttpResponseForbidden()
        return super().post(request, *args, **kwargs)


#
# Step 0: welcome screen
#
class Step0WelcomeView(WizardStepMixin, FormView):
    template_name = 'YtManagerApp/first_time_setup/step0_welcome.html'
    form_class = WelcomeForm
    success_url = reverse_lazy('first_time_1')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'config_errors': settings.CONFIG_ERRORS,
            'config_warnings': settings.CONFIG_WARNINGS,
        })
        return context


#
# Step 1: setup API key
#
class Step1ApiKeyView(WizardStepMixin, FormView):
    template_name = 'YtManagerApp/first_time_setup/step1_apikey.html'
    form_class = ApiKeyForm
    success_url = reverse_lazy('first_time_2')

    def get_initial(self):
        initial = super().get_initial()
        initial['api_key'] = Services.appConfig().youtube_api_key
        return initial

    def form_valid(self, form):
        key = form.cleaned_data['api_key']
        # TODO: validate key
        if key is not None and len(key) > 0:
            Services.appConfig().youtube_api_key = key

        return super().form_valid(form)


#
# Step 2: create admin user
#
class Step2SetupAdminUserView(WizardStepMixin, FormView):
    template_name = 'YtManagerApp/first_time_setup/step2_admin.html'
    success_url = reverse_lazy('first_time_3')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_form_class(self):
        have_users = User.objects.count() > 0
        have_admin = User.objects.filter(is_superuser=True).count() > 0

        # Check if an admin user already exists
        if have_admin:
            logger.debug("Admin user already exists and is not logged in!")
            return LoginForm

        elif have_users and 'register' not in self.kwargs:
            logger.debug("There are users but no admin!")
            return PickAdminUserForm

        logger.debug("No admin user exists, will register a new account!")
        return UserCreationForm

    def get(self, request, *args, **kwargs):

        # Skip if admin is already logged in
        if request.user.is_authenticated and request.user.is_superuser:
            logger.debug("Admin user already exists and is logged in!")
            return redirect(self.success_url)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        if isinstance(form, LoginForm):
            form.apply_session_expiry(self.request)
            login(self.request, form.get_user())

        elif isinstance(form, UserCreationForm):
            user = form.save()
            user.is_staff = True
            user.is_superuser = True
            user.save()

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(self.request, user)

        elif isinstance(form, PickAdminUserForm):
            user = form.cleaned_data['admin_user']
            user.is_staff = True
            user.is_superuser = True
            user.save()

            return redirect('first_time_2', assigned_success='1')

        return super().form_valid(form)


#
# Step 3: configure server
#
class Step3ConfigureView(WizardStepMixin, FormView):
    template_name = 'YtManagerApp/first_time_setup/step3_configure.html'
    form_class = ServerConfigForm
    success_url = reverse_lazy('first_time_done')

    def get_initial(self):
        initial = super().get_initial()
        initial['allow_registrations'] = Services.appConfig().allow_registrations
        initial['sync_schedule'] = Services.appConfig().sync_schedule
        initial['auto_download'] = self.request.user.preferences['auto_download']
        initial['download_location'] = self.request.user.preferences['download_path']
        return initial

    def form_valid(self, form):
        allow_registrations = form.cleaned_data['allow_registrations']
        if allow_registrations is not None:
            Services.appConfig().allow_registrations = allow_registrations

        sync_schedule = form.cleaned_data['sync_schedule']
        if sync_schedule is not None and len(sync_schedule) > 0:
            Services.appConfig().sync_schedule = sync_schedule

        auto_download = form.cleaned_data['auto_download']
        if auto_download is not None:
            self.request.user.preferences['auto_download'] = auto_download

        download_location = form.cleaned_data['download_location']
        if download_location is not None and len(download_location) > 0:
            self.request.user.preferences['download_path'] = download_location

        # Set initialized to true
        Services.appConfig().initialized = True

        # Start scheduler if not started
        Services.scheduler.initialize()
        SynchronizeJob.schedule_global_job()

        return super().form_valid(form)


#
# Done screen
#
class DoneView(FormView):
    template_name = 'YtManagerApp/first_time_setup/done.html'
    form_class = DoneForm
    success_url = reverse_lazy('home')
