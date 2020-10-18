from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from YtManagerApp.providers.video_provider import VideoProviderState
from YtManagerApp.services import Services
from collections import namedtuple

VideoProviderInfoViewModel = namedtuple('VideoProviderInfoViewModel',
                                        ['id', 'name', 'is_configured', 'has_error', 'image_src'])


class ProvidersView(LoginRequiredMixin, TemplateView):
    template_name = 'YtManagerApp/settings/providers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        providers = []
        have_unconfigured = False
        have_configured = False

        for provider in Services.videoProviderManager().get_available_providers():
            providers.append(VideoProviderInfoViewModel(
                id=provider.id,
                name=provider.name,
                is_configured=provider.state != VideoProviderState.NOT_CONFIGURED,
                has_error=provider.state == VideoProviderState.ERROR,
                image_src=f"YtManagerApp/img/video_providers/{provider.id}.png"
            ))

            if provider.state != VideoProviderState.NOT_CONFIGURED:
                have_configured = True
            if provider.state == VideoProviderState.NOT_CONFIGURED:
                have_unconfigured = True

        context['providers'] = sorted(providers, key=lambda x: x.name)
        context['have_unconfigured'] = have_unconfigured
        context['have_configured'] = have_configured
        return context
