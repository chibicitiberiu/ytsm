import dependency_injector.containers as containers
import dependency_injector.providers as providers
from dynamic_preferences.registries import global_preferences_registry
from YtManagerApp.management.appconfig import AppConfig
from YtManagerApp.management.youtube_dl_manager import YoutubeDlManager
from YtManagerApp.scheduler.scheduler import YtsmScheduler


class Services(containers.DeclarativeContainer):
    globalPreferencesRegistry = providers.Object(global_preferences_registry.manager())
    appConfig = providers.Singleton(AppConfig, globalPreferencesRegistry)
    scheduler = providers.Singleton(YtsmScheduler, appConfig)
    youtubeDLManager = providers.Singleton(YoutubeDlManager)
