from django.contrib.auth.models import User
from django.db import models

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
