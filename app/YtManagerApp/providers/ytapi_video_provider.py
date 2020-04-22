from typing import Dict, Optional, Any, Iterable, List

from django import forms
from external.pytaw.pytaw import youtube as yt
from external.pytaw.pytaw.utils import iterate_chunks

from YtManagerApp.models import Subscription, Video
from YtManagerApp.providers.video_provider import VideoProvider, InvalidURLError


class YouTubeApiVideoProvider(VideoProvider):
    id = "YtAPI"
    name = "YouTube API"
    description = "Allows communication with YouTube using the YouTube API."
    settings = {
        "api_key": forms.CharField(label="YouTube API Key:")
    }

    def __init__(self):
        super().__init__()
        self.__api_key: str = None
        self.__api: yt.YouTube = None

    def configure(self, configuration: Dict[str, Any]) -> None:
        self.__api_key = configuration['api_key']
        self.__api = yt.YouTube(key=self.__api_key)

    def validate_configuration(self, configuration: Dict[str, Any]):
        # TODO: implement
        pass

    def get_subscription_url(self, subscription: Subscription):
        return f"https://youtube.com/playlist?list={subscription.playlist_id}"

    def validate_subscription_url(self, url: str) -> None:
        try:
            parsed_url = self.__api.parse_url(url)
        except yt.InvalidURL:
            raise InvalidURLError("The given URL is not valid!")

        is_playlist = 'playlist' in parsed_url
        is_channel = parsed_url['type'] in ('channel', 'user', 'channel_custom')

        if not is_channel and not is_playlist:
            raise InvalidURLError('The given URL is not a channel or a playlist!')

    def fetch_subscription(self, url: str) -> Subscription:
        sub = Subscription()
        sub.provider_id = self.id

        self.validate_subscription_url(url)
        url_parsed = self.__api.parse_url(url)

        if 'playlist' in url_parsed:
            info_playlist = self.__api.playlist(url=url)
            if info_playlist is None:
                raise ValueError('Invalid playlist ID!')

            sub.name = info_playlist.title
            sub.playlist_id = info_playlist.id
            sub.description = info_playlist.description
            sub.channel_id = info_playlist.channel_id
            sub.channel_name = info_playlist.channel_title
            sub.thumbnail = self._best_thumbnail(info_playlist).url

        else:
            info_channel = self.__api.channel(url=url)
            if info_channel is None:
                raise ValueError('Cannot find channel!')

            sub.name = info_channel.title
            sub.playlist_id = info_channel.uploads_playlist.id
            sub.description = info_channel.description
            sub.channel_id = info_channel.id
            sub.channel_name = info_channel.title
            sub.thumbnail = self._best_thumbnail(info_channel).url
            sub.rewrite_playlist_indices = True

        return sub

    def _default_thumbnail(self, resource: yt.Resource) -> Optional[yt.Thumbnail]:
        """
        Gets the default thumbnail for a resource.
        Searches in the list of thumbnails for one with the label 'default', or takes the first one.
        :param resource:
        :return:
        """
        thumbs = getattr(resource, 'thumbnails', None)

        if thumbs is None or len(thumbs) <= 0:
            return None

        return next(
            (i for i in thumbs if i.id == 'default'),
            thumbs[0]
        )

    def _best_thumbnail(self, resource: yt.Resource) -> Optional[yt.Thumbnail]:
        """
        Gets the best thumbnail available for a resource.
        :param resource:
        :return:
        """
        thumbs = getattr(resource, 'thumbnails', None)

        if thumbs is None or len(thumbs) <= 0:
            return None

        return max(thumbs, key=lambda t: t.width * t.height)

    def get_video_url(self, video: Video) -> str:
        return f"https://youtube.com/watch?v={video.video_id}"

    def fetch_videos(self, subscription: Subscription) -> Iterable[Video]:
        playlist_items = self.__api.playlist_items(subscription.playlist_id)
        for item in playlist_items:
            video = Video()
            video.video_id = item.resource_video_id
            video.name = item.title
            video.description = item.description
            video.watched = False
            video.new = True
            video.downloaded_path = None
            video.subscription = subscription
            video.playlist_index = item.position
            video.publish_date = item.published_at
            video.thumbnail = self._best_thumbnail(item).url
            yield video

    def update_videos(self, videos: List[Video], update_metadata=False, update_statistics=False) -> None:
        parts = ['id']
        if update_metadata:
            parts.append('snippet')
        if update_statistics:
            parts.append('statistics')

        # don't waste api resources
        if len(parts) <= 1:
            return

        video_dict = {video.video_id: video for video in videos}
        id_list = video_dict.keys()

        for batch in iterate_chunks(id_list, 50):
            resp_videos = self.__api.videos(batch, part=','.join(parts))
            for resp_video in resp_videos:
                v = video_dict[resp_video.id]

                if update_metadata:
                    v.name = resp_video.title
                    v.description = resp_video.description

                if update_statistics:
                    if resp_video.n_likes is not None \
                            and resp_video.n_dislikes is not None \
                            and resp_video.n_likes + resp_video.n_dislikes > 0:
                        v.rating = resp_video.n_likes / (resp_video.n_likes + resp_video.n_dislikes)
                    v.views = resp_video.n_views
