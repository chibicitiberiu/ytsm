import json
from typing import ClassVar, Iterable, Optional

from django import forms
from external.pytaw.pytaw.utils import iterate_chunks
from external.pytaw.pytaw.youtube import YouTube, Thumbnail, InvalidURL, Resource, Video

from YtManagerApp.models import Video, Subscription
from YtManagerApp.services.providers.video_provider import VideoProvider
from YtManagerApp.services.scheduler.progress_tracker import ProgressTracker


class YouTubeConfigForm(forms.Form):
    api_key = forms.CharField(label="YouTube API Key:")


class YouTubeProvider(VideoProvider):

    def __init__(self):
        self._apiKey: str = None
        self._api: YouTube = None

    def _sanity_check(self):
        if self._apiKey is None:
            raise ValueError("The YouTube API key is not set!")

    @staticmethod
    def _best_thumbnail(resource: Resource) -> Optional[Thumbnail]:
        """
        Gets the best thumbnail available for a resource.
        :param resource:
        :return:
        """
        thumbs = getattr(resource, 'thumbnails', None)

        if thumbs is None or len(thumbs) <= 0:
            return None

        return max(thumbs, key=lambda t: t.width * t.height)

    def update_configuration(self, **kwargs):
        self._apiKey = kwargs.get('apiKey')
        self._sanity_check()
        self._api = YouTube(key=self._apiKey)

    def get_display_name(self) -> str:
        return "YouTube API Provider"

    def get_provider_id(self) -> str:
        return 'youtube'

    def validate_playlist_url(self, url: str) -> bool:
        try:
            parsed_url = self._api.parse_url(url)
        except InvalidURL:
            return False

        is_playlist = 'playlist' in parsed_url
        is_channel = parsed_url['type'] in ('channel', 'user', 'channel_custom')

        return is_playlist or is_channel

    def fetch_playlist(self, url: str) -> Subscription:

        if not self.validate_playlist_url(url):
            raise ValueError("Invalid playlist or channel URL")

        parsed_url = self._api.parse_url(url)
        sub = Subscription()

        if 'playlist' in parsed_url:
            info = self._api.playlist(url=url)
            if info is None:
                raise ValueError('Invalid playlist ID!')
            provider_data = {
                'channel_id': None,
                'rewrite_indices': False
            }
            sub.provider_id = info.id

        else:
            info = self._api.channel(url=url)
            if info is None:
                raise ValueError('Cannot find channel!')

            provider_data = {
                'channel_id': info.id,
                'rewrite_indices': True
            }
            sub.provider_id = info.uploads_playlist.id

        sub.name = info.title
        sub.description = info.description
        sub.original_url = url
        sub.thumbnail = YouTubeProvider._best_thumbnail(info).url

        sub.provider = self.get_provider_id()
        sub.provider_data = json.dumps(provider_data)

        return sub

    def fetch_videos(self, subscription: Subscription) -> Iterable[Video]:
        provider_data = json.loads(subscription.provider_data)
        playlist_items = self._api.playlist_items(subscription.provider_id)

        if provider_data.get('rewrite_indices'):
            playlist_items = sorted(playlist_items, key=lambda x: x.published_at)
        else:
            playlist_items = sorted(playlist_items, key=lambda x: x.position)
        i = 1

        for playlist_item in playlist_items:
            video = Video()
            video.name = playlist_item.title
            video.description = playlist_item.description
            video.publish_date = playlist_item.published_at
            video.thumbnail = YouTubeProvider._best_thumbnail(playlist_item).url
            video.uploader_name = ""

            video.provider_id = playlist_item.resource_video_id
            video.provider_data = None

            if provider_data.get('rewrite_indices'):
                video.playlist_index = i
                i += 1
            else:
                video.playlist_index = playlist_item.position
            video.downloaded_path = None
            video.subscription = subscription

            video.watched = False
            video.new = True

            yield video

    def update_videos(self, videos: Iterable[Video], progress_tracker: ProgressTracker, update_info: bool = True, update_stats: bool = False):
        videos_list = list(videos)
        progress_tracker.total_steps = len(videos_list)

        parts = 'id'
        if update_info:
            parts += ',snippet'
        if update_stats:
            parts += ',statistics'

        for batch in iterate_chunks(videos_list, 50):
            batch_ids = [video.video_id for video in batch]
            videos_new = {v.id: v for v in self._api.videos(batch_ids, part=parts)}

            for video in batch:
                progress_tracker.advance(1, "Updating video " + video.name)
                video_new = videos_new.get(video.provider_id)
                if video_new is None:
                    continue

                if update_info:
                    video.name = video_new.title
                    video.description = video_new.description
                if update_stats:
                    if video_new.n_likes is not None \
                            and video_new.n_dislikes is not None \
                            and video_new.n_likes + video_new.n_dislikes > 0:
                        video.rating = video_new.n_likes / (video_new.n_likes + video_new.n_dislikes)
                    video.views = video_new.n_views

    def get_config_form(self) -> ClassVar[forms.Form]:
        return YouTubeConfigForm
