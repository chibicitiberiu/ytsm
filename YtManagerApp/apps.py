from django.apps import AppConfig
import os


class YtManagerAppConfig(AppConfig):
    name = 'YtManagerApp'

    def ready(self):
        # There seems to be a problem related to the auto-reload functionality where ready() is called twice
        # (in different processes). This seems like a good enough workaround (other than --noreload).
        if not os.getenv('RUN_MAIN', False):
            from .appmain import main
            main()
