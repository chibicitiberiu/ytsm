from YtManagerApp.services.providers.video_provider import VideoProvider


class VideoProviderManager(object):

    def __init__(self):
        self._providers: Dict[str, VideoProvider] = {}

    def register_provider(self, provider: VideoProvider):
        pid = provider.get_provider_id()
        self._providers[pid] = provider
