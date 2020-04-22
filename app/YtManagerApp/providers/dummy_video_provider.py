from typing import Dict, Optional, Any, Iterable, List

from django import forms
from external.pytaw.pytaw import youtube as yt
from external.pytaw.pytaw.utils import iterate_chunks

from YtManagerApp.models import Subscription, Video
from YtManagerApp.providers.video_provider import VideoProvider, InvalidURLError, ProviderValidationError


class DummyVideoProvider(VideoProvider):
    id = "Dummy"
    name = "Dummy Videos"
    description = "Won't really do anything, it's here just for testing."
    settings = {
        "api_key": forms.CharField(label="Dummy API Key"),
        "number_of_something": forms.IntegerField(label="Number of stuff")
    }

    def configure(self, configuration: Dict[str, Any]) -> None:
        print(configuration)

    def validate_configuration(self, configuration: Dict[str, Any]):
        print("Validating...")
        if configuration["number_of_something"] >= 10:
            raise ProviderValidationError(
                field_messages={'number_of_something': "Number too large, try something smaller!"})
        pass

    def get_subscription_url(self, subscription: Subscription):
        return f"https://dummy/playlist/{subscription.playlist_id}"

    def validate_subscription_url(self, url: str) -> None:
        if not url.startswith('https://dummy/'):
            raise InvalidURLError("URL not valid")

    def fetch_subscription(self, url: str) -> Subscription:
        raise ValueError('No such subscription (note: dummy plugin, nothing will work)!')

    def get_video_url(self, video: Video) -> str:
        return f"https://dummy/video/{video.video_id}"

    def fetch_videos(self, subscription: Subscription) -> Iterable[Video]:
        return []

    def update_videos(self, videos: List[Video], update_metadata=False, update_statistics=False) -> None:
        pass
