import mimetypes
import os

from django.db import models

from .subscription import Subscription


class Video(models.Model):
    video_id = models.CharField(null=False, max_length=12)
    name = models.TextField(null=False)
    description = models.TextField()
    watched = models.BooleanField(default=False, null=False)
    new = models.BooleanField(default=True, null=False)
    downloaded_path = models.TextField(null=True, blank=True)
    downloaded_size = models.IntegerField(null=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    playlist_index = models.IntegerField(null=False)
    publish_date = models.DateTimeField(null=False)
    last_updated_date = models.DateTimeField(null=False, auto_now=True)
    thumbnail = models.TextField()
    uploader_name = models.CharField(null=False, max_length=255)
    views = models.IntegerField(null=False, default=0)
    rating = models.FloatField(null=False, default=0.5)

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

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'video {self.id}, video_id="{self.video_id}"'
