from django.db import models


class SubscriptionFolder(models.Model):
    name = models.TextField(null=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Channel(models.Model):
    channel_id = models.TextField(null=False, unique=True)
    username = models.TextField(null=True, unique=True)
    custom_url = models.TextField(null=True, unique=True)
    name = models.TextField()
    description = models.TextField()
    icon_default = models.TextField()
    icon_best = models.TextField()
    upload_playlist_id = models.TextField()

    @staticmethod
    def find_by_channel_id(channel_id):
        result = Channel.objects.filter(channel_id=channel_id)
        if len(result) > 0:
            return result.first()
        return None

    @staticmethod
    def find_by_username(username):
        result = Channel.objects.filter(username=username)
        if len(result) > 0:
            return result.first()
        return None

    @staticmethod
    def find_by_custom_url(custom_url):
        result = Channel.objects.filter(custom_url=custom_url)
        if len(result) > 0:
            return result.first()
        return None

    def __str__(self):
        return self.name


class Subscription(models.Model):
    name = models.TextField(null=False)
    parent_folder = models.ForeignKey(SubscriptionFolder, on_delete=models.SET_NULL, null=True, blank=True)
    playlist_id = models.TextField(null=False, unique=True)
    description = models.TextField()
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    icon_default = models.TextField()
    icon_best = models.TextField()

    def __str__(self):
        return self.name


class Video(models.Model):
    video_id = models.TextField(null=False)
    name = models.TextField(null=False)
    description = models.TextField()
    watched = models.BooleanField(default=False, null=False)
    downloaded_path = models.TextField(null=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    playlist_index = models.IntegerField(null=False)
    publish_date = models.DateTimeField(null=False)
    icon_default = models.TextField()
    icon_best = models.TextField()

    def __str__(self):
        return self.name