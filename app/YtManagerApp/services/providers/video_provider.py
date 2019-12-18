from abc import abstractmethod, ABC
from typing import Iterable, ClassVar

from django import forms

from YtManagerApp.models import Subscription, Video
from YtManagerApp.services.scheduler.progress_tracker import ProgressTracker


class VideoProvider(ABC):
    """
    Represents a video hosting service that provides videos and playlists (e.g. YouTube, Vimeo).
    Note: the method implementations should be thread safe, as they may be called from multiple jobs running in
    parallel.
    """

    @abstractmethod
    def update_configuration(self, **kwargs):
        """
        Updates the configuration options of this video provider.
        This method is called first when the provider is registered using the configuration stored in the
        database. After that, the method will be called when the user changes any configuration options.
        :param kwargs: Configuration arguments
        """
        pass

    @abstractmethod
    def get_display_name(self) -> str:
        """
        Returns an user friendly name for this provider.
        :return:
        """
        pass

    @abstractmethod
    def get_provider_id(self) -> str:
        """
        Returns an identifier that uniquely identifies this provider.
        :return:
        """
        pass

    @abstractmethod
    def validate_playlist_url(self, url: str) -> bool:
        """
        Validates that the given playlist URL is valid for the given video provider service.
        :param url:
        :return:
        """
        pass

    @abstractmethod
    def fetch_playlist(self, url: str) -> Subscription:
        """
        Gets metadata about the playlist identified by the given URL.
        :param url:
        :return:
        """
        pass

    @abstractmethod
    def fetch_videos(self, subscription: Subscription) -> Iterable[Video]:
        """
        Gets metadata about the videos in the given playlist.
        :param subscription:
        :return:
        """
        pass

    @abstractmethod
    def update_videos(self, videos: Iterable[Video], progress_tracker: ProgressTracker, update_info: bool = True, update_stats: bool = False):
        """
        Updates metadata about given videos.
        :param update_info: If set to true, basic information such as title, description will be updated
        :param update_stats: If set to true, video statistics (such as rating, view counts) will be updated
        :param videos: Videos to be updated.
        :param progress_tracker: Used to track the progress of the update process
        :return:
        """
        pass

    @abstractmethod
    def get_config_form(self) -> ClassVar[forms.Form]:
        """
        Gets the configuration form
        :return:
        """
        pass
