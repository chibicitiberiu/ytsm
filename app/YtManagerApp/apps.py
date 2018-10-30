from django.apps import AppConfig
import os


class YtManagerAppConfig(AppConfig):
    name = 'YtManagerApp'

    def ready(self):
        # Run server using --noreload to avoid having the scheduler run on 2 different processes
        from .appmain import main
        main()
