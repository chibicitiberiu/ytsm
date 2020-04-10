from django.db import models


class VideoProviderConfig(models.Model):
    provider_id = models.CharField(max_length=128, unique=True, help_text="Provider ID")
    settings = models.TextField(help_text="Video provider settings")
