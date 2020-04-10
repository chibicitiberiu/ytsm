from django.contrib.auth.models import User
from django.db import models

from .subscription_folder import SubscriptionFolder
from .video_order import VIDEO_ORDER_CHOICES


class Subscription(models.Model):
    name = models.CharField(null=False, max_length=1024)
    parent_folder = models.ForeignKey(SubscriptionFolder, on_delete=models.CASCADE, null=True, blank=True)
    provider_id = models.CharField(max_length=128, null=False)
    playlist_id = models.CharField(null=False, max_length=128)
    description = models.TextField()
    channel_id = models.CharField(max_length=128)
    channel_name = models.CharField(max_length=1024)
    thumbnail = models.CharField(max_length=1024)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # youtube adds videos to the 'Uploads' playlist at the top instead of the bottom
    rewrite_playlist_indices = models.BooleanField(null=False, default=False)

    # overrides
    auto_download = models.BooleanField(null=True, blank=True)
    download_limit = models.IntegerField(null=True, blank=True)
    download_order = models.CharField(
        null=True, blank=True,
        max_length=128,
        choices=VIDEO_ORDER_CHOICES)
    automatically_delete_watched = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'subscription {self.id}, name="{self.name}", playlist_id="{self.playlist_id}"'

    def delete_subscription(self, keep_downloaded_videos: bool):
        self.delete()

    def copy_from(self, other: "Subscription"):
        self.name = other.name
        self.parent_folder = other.parent_folder
        self.provider_id = other.provider_id
        self.playlist_id = other.playlist_id
        self.description = other.description
        self.channel_id = other.channel_id
        self.channel_name = other.channel_name
        self.thumbnail = other.thumbnail
        try:
            self.user = other.user
        except User.DoesNotExist:
            self.user = None

        self.rewrite_playlist_indices = other.rewrite_playlist_indices

        self.auto_download = other.auto_download
        self.download_limit = other.download_limit
        self.download_order = other.download_order
        self.automatically_delete_watched = other.automatically_delete_watched
