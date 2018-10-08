from django.apps import AppConfig


class YtManagerAppConfig(AppConfig):
    name = 'YtManagerApp'

    def ready(self):
        from .management import SubscriptionManager
        SubscriptionManager.start_scheduler()
