from django.db import models

class SubscriptionFolder(models.Model):
    name = models.TextField(null=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    name = models.TextField(null=False)
    parent_folder = models.ForeignKey(SubscriptionFolder, on_delete=models.SET_NULL, null=True, blank=True)
    url = models.TextField(null=False, unique=True)
    
    def __str__(self):
        return self.name


class Video(models.Model):
    name = models.TextField(null=False)
    ytid = models.TextField(null=False)
    downloaded_path = models.TextField(null=True, blank=True)
    watched = models.BooleanField(default=False, null=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)

    def __str__(self):
        return self.name