import logging
import mimetypes
import os
from typing import Callable, Union, Any, Optional

from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Lower

# help_text = user shown text
# verbose_name = user shown name
# null = nullable, blank = user is allowed to set value to empty
VIDEO_ORDER_CHOICES = [
    ('newest', 'Newest'),
    ('oldest', 'Oldest'),
    ('playlist', 'Playlist order'),
    ('playlist_reverse', 'Reverse playlist order'),
    ('popularity', 'Popularity'),
    ('rating', 'Top rated'),
]

VIDEO_ORDER_MAPPING = {
    'newest': '-publish_date',
    'oldest': 'publish_date',
    'playlist': 'playlist_index',
    'playlist_reverse': '-playlist_index',
    'popularity': '-views',
    'rating': '-rating'
}


class Provider(models.Model):

    class_name = models.CharField(null=False, max_length=64, unique=True,
                                  help_text='Class name in the "providers" package.')

    config = models.CharField(max_length=1024,
                              help_text='Provider configuration (stored as JSON)')


class SubscriptionFolder(models.Model):

    name = models.CharField(null=False, max_length=250,
                            help_text='Folder name')

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               help_text='Parent folder')

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False,
                             help_text='User who owns the subscription')

    class Meta:
        ordering = [Lower('parent__name'), Lower('name')]

    def __str__(self):
        s = ""
        current = self
        while current is not None:
            s = current.name + " > " + s
            current = current.parent
        return s[:-3]

    def __repr__(self):
        return f'folder {self.id}, name="{self.name}"'

    def delete_folder(self, keep_subscriptions: bool):
        if keep_subscriptions:

            def visit(node: Union["SubscriptionFolder", "Subscription"]):
                if isinstance(node, Subscription):
                    node.parent_folder = None
                    node.save()

            SubscriptionFolder.traverse(self.id, self.user, visit)

        self.delete()

    @staticmethod
    def traverse(root_folder_id: Optional[int],
                 user: User,
                 visit_func: Callable[[Union["SubscriptionFolder", "Subscription"]], Any]):

        data_collected = []

        def collect(data):
            if data is not None:
                data_collected.append(data)

        # Visit root
        if root_folder_id is not None:
            root_folder = SubscriptionFolder.objects.get(id=root_folder_id)
            collect(visit_func(root_folder))

        queue = [root_folder_id]
        visited = []

        while len(queue) > 0:
            folder_id = queue.pop()

            if folder_id in visited:
                logging.error('Found folder tree cycle for folder id %d.', folder_id)
                continue
            visited.append(folder_id)

            for folder in SubscriptionFolder.objects.filter(parent_id=folder_id, user=user).order_by(Lower('name')):
                collect(visit_func(folder))
                queue.append(folder.id)

            for subscription in Subscription.objects.filter(parent_folder_id=folder_id, user=user).order_by(Lower('name')):
                collect(visit_func(subscription))

        return data_collected


class Subscription(models.Model):
    name = models.CharField(null=False, max_length=1024,
                            help_text='Name of playlist or channel.')

    description = models.TextField(help_text='Description of the playlist/channel.')

    original_url = models.CharField(null=False, max_length=1024,
                                    help_text='Original URL added by user.')

    thumbnail = models.CharField(max_length=1024,
                                 help_text='An URL to the thumbnail.')

    #
    provider = models.ForeignKey(Provider, null=True, on_delete=models.SET_DEFAULT,
                                 help_text='Provider who manages this subscription (e.g. YouTube, Vimeo etc)')

    provider_id = models.CharField(null=False, max_length=64,
                                   help_text='Identifier according to provider (e.g. YouTube video ID)')

    provider_data = models.CharField(null=True, max_length=1024,
                                     help_text='Extra data stored by the provider serialized as JSON')

    #
    parent_folder = models.ForeignKey(SubscriptionFolder, on_delete=models.CASCADE, null=True, blank=True,
                                      help_text='Parent folder')

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             help_text='Owner user')

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


class Video(models.Model):
    name = models.TextField(null=False)
    description = models.TextField()
    publish_date = models.DateTimeField(null=False)
    thumbnail = models.TextField()
    uploader_name = models.CharField(null=False, max_length=255)

    provider_id = models.CharField(null=False, max_length=64)
    provider_data = models.CharField(null=True, max_length=1024)

    playlist_index = models.IntegerField(null=False)
    downloaded_path = models.TextField(null=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)

    watched = models.BooleanField(default=False, null=False)
    new = models.BooleanField(default=True, null=False)

    views = models.IntegerField(null=False, default=0)
    rating = models.FloatField(null=False, default=0.5)

    def mark_watched(self):
        self.watched = True
        self.save()
        if self.downloaded_path is not None:
            from YtManagerApp.management.appconfig import appconfig
            from YtManagerApp.management.scheduler.jobs import DeleteVideoJob
            from YtManagerApp.management.scheduler.jobs import SynchronizeJob

            if appconfig.for_sub(self.subscription, 'automatically_delete_watched'):
                DeleteVideoJob.schedule(self)
                SynchronizeJob.schedule_now_for_subscription(self.subscription)

    def mark_unwatched(self):
        self.watched = False
        self.save()
        from YtManagerApp.management.scheduler.jobs.synchronize_job import SynchronizeJob
        SynchronizeJob.schedule_now_for_subscription(self.subscription)

    def get_files(self):
        if self.downloaded_path is not None:
            directory, file_pattern = os.path.split(self.downloaded_path)
            for file in os.listdir(directory):
                if file.startswith(file_pattern):
                    yield os.path.join(directory, file)

    def find_video(self):
        """
        Finds the video file from the downloaded files, and
        returns
        :return: Tuple containing file path and mime type
        """
        for file in self.get_files():
            mime, _ = mimetypes.guess_type(file)
            if mime is not None and mime.startswith('video/'):
                return file, mime

        return None, None

    def delete_files(self):
        if self.downloaded_path is not None:
            from YtManagerApp.management.scheduler.jobs import DeleteVideoJob
            from YtManagerApp.management.appconfig import appconfig
            from YtManagerApp.management.scheduler.jobs import SynchronizeJob

            DeleteVideoJob.schedule(self)

            # Mark watched?
            if self.subscription.user.preferences['mark_deleted_as_watched']:
                self.watched = True
                SynchronizeJob.schedule_now_for_subscription(self.subscription)

    def download(self):
        if not self.downloaded_path:
            from YtManagerApp.management.scheduler.jobs import DownloadVideoJob
            DownloadVideoJob.schedule(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'video {self.id}, video_id="{self.video_id}"'


JOB_STATES = [
    ('running', 0),
    ('finished', 1),
    ('failed', 2),
    ('interrupted', 3),
]

JOB_STATES_MAP = {
    'running': 0,
    'finished': 1,
    'failed': 2,
    'interrupted': 3,
}

JOB_MESSAGE_LEVELS = [
    ('normal', 0),
    ('warning', 1),
    ('error', 2),
]
JOB_MESSAGE_LEVELS_MAP = {
    'normal': 0,
    'warning': 1,
    'error': 2,
}


class JobExecution(models.Model):
    start_date = models.DateTimeField(auto_now=True, null=False)
    end_date = models.DateTimeField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    description = models.CharField(max_length=250, null=False, default="")
    status = models.IntegerField(choices=JOB_STATES, null=False, default=0)


class JobMessage(models.Model):
    timestamp = models.DateTimeField(auto_now=True, null=False)
    job = models.ForeignKey(JobExecution, null=False, on_delete=models.CASCADE)
    progress = models.FloatField(null=True)
    message = models.CharField(max_length=1024, null=False, default="")
    level = models.IntegerField(choices=JOB_MESSAGE_LEVELS, null=False, default=0)
    suppress_notification = models.BooleanField(null=False, default=False)
