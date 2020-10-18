import json
import logging
from typing import List, Dict, Union, Iterable, Optional

from django.db import transaction

from YtManagerApp.models import VideoProviderConfig, Video, Subscription
from YtManagerApp.providers.video_provider import VideoProvider, InvalidURLError, VideoProviderState

log = logging.getLogger("VideoProviderManager")


class VideoProviderManager(object):
    def __init__(self, registered_providers: List[VideoProvider]):
        self._registered_providers: Dict[str, VideoProvider] = {}
        self._pending_configs: Dict[str, VideoProviderConfig] = {}

        for rp in registered_providers:
            self.register_provider(rp)
        self._load()

    def register_provider(self, provider: VideoProvider) -> None:
        """
        Registers a video provider
        :param provider: Video provider
        """
        # avoid duplicates
        if provider.id in self._registered_providers:
            log.error(f"Duplicate video provider {provider.id}")
            return

        # register
        self._registered_providers[provider.id] = provider
        log.info(f"Registered video provider {provider.id}")

        # load configuration (if any)
        if provider.id in self._pending_configs:
            self._configure(provider, self._pending_configs[provider.id])
            del self._pending_configs[provider.id]

    def configure_provider(self, provider_id: str, config: Optional[Dict[str, any]]):
        provider = self.get(provider_id)

        if config is not None:
            provider.configure(config)
            with transaction.atomic():
                cfg, _ = VideoProviderConfig.objects.get_or_create(provider_id=provider_id)
                cfg.settings = json.dumps(config)
                cfg.save()
            provider.state = VideoProviderState.OK

        else:
            provider.unconfigure()
            VideoProviderConfig.objects.filter(provider_id=provider_id).delete()
            provider.state = VideoProviderState.NOT_CONFIGURED

    def get_provider_config(self, provider_id: str):
        cfg = VideoProviderConfig.objects.filter(provider_id=provider_id).first()
        if cfg is not None:
            return json.loads(cfg.settings)
        return None

    def _load(self) -> None:
        # Loads configuration from database
        for config in VideoProviderConfig.objects.all():
            provider = self._registered_providers.get(config.provider_id)

            # provider not yet registered, keep it in the pending list
            if provider is None:
                self._pending_configs[config.provider_id] = config
                log.warning(f"Provider {config.provider_id} not registered!")
                continue

            # configure
            self._configure(provider, config)

    def _configure(self, provider, config):
        settings = json.loads(config.settings)
        provider.configure(settings)
        provider.state = VideoProviderState.OK
        log.info(f"Configured video provider {provider.id}")

    def get(self, item: Union[str, Subscription, Video]):
        """
        Gets provider for given item (subscription or video).
        :param item: Provider ID, or subscription, or video
        :return: Provider
        """
        if isinstance(item, str):
            return self._registered_providers[item]
        elif isinstance(item, Video):
            return self._registered_providers[item.subscription.provider_id]
        elif isinstance(item, Subscription):
            return self._registered_providers[item.provider_id]
        return None

    def validate_subscription_url(self, url: str):
        """
        Validates given URL using all registered and configured provider.
        :param url:
        :return:
        """
        for provider in self._registered_providers.values():
            if provider.state == VideoProviderState.OK:
                try:
                    provider.validate_subscription_url(url)
                    return
                except InvalidURLError:
                    pass

        raise InvalidURLError("The given URL is not valid for any of the supported sites!")

    def fetch_subscription(self, url: str) -> Subscription:
        """
        Validates given URL using all registered and configured provider.
        :param url:
        :return:
        """
        for provider in self._registered_providers.values():
            if provider.state == VideoProviderState.OK:
                try:
                    provider.validate_subscription_url(url)
                    # Found the right provider
                    return provider.fetch_subscription(url)
                except InvalidURLError:
                    pass

        raise InvalidURLError("The given URL is not valid for any of the supported sites!")

    def get_available_providers(self) -> Iterable[VideoProvider]:
        return self._registered_providers.values()
