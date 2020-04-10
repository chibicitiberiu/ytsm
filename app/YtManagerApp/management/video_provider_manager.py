import logging
from typing import List, Dict, Union

from YtManagerApp.models import VideoProviderConfig, Video, Subscription
from YtManagerApp.providers.video_provider import VideoProvider, InvalidURLError
import json

log = logging.getLogger("VideoProviderManager")


class VideoProviderManager(object):
    def __init__(self, registered_providers: List[VideoProvider]):
        self._registered_providers: Dict[str, VideoProvider] = {}
        self._configured_providers: Dict[str, VideoProvider] = {}
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
        if provider.name in self._registered_providers:
            log.error(f"Duplicate video provider {provider.name}")
            return

        # register
        self._registered_providers[provider.name] = provider
        log.info(f"Registered video provider {provider.name}")

        # load configuration (if any)
        if provider.name in self._pending_configs:
            self._configure(provider, self._pending_configs[provider.name])
            del self._pending_configs[provider.name]

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
        log.info(f"Configured video provider {provider.name}")
        self._configured_providers[provider.name] = provider

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
        for provider in self._configured_providers.values():
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
        for provider in self._configured_providers.values():
            try:
                provider.validate_subscription_url(url)
                # Found the right provider
                return provider.fetch_subscription(url)
            except InvalidURLError:
                pass

        raise InvalidURLError("The given URL is not valid for any of the supported sites!")
