from django.contrib import admin
from .models import SubscriptionFolder, Subscription, Video

admin.site.register(SubscriptionFolder)
admin.site.register(Subscription)
admin.site.register(Video)
