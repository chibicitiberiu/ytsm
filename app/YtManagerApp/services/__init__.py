import dependency_injector.containers as di_containers
import dependency_injector.providers as di_providers
from dynamic_preferences.registries import global_preferences_registry
from YtManagerApp.services.appconfig import AppConfig
from YtManagerApp.services.youtube_dl_manager import YoutubeDlManager
from YtManagerApp.services.scheduler.scheduler import YtsmScheduler
from YtManagerApp.services.video_provider_manager import VideoProviderManager


class Services(di_containers.DeclarativeContainer):
    globalPreferencesRegistry = di_providers.Object(global_preferences_registry.manager())
    appConfig = di_providers.Singleton(AppConfig, globalPreferencesRegistry)
    scheduler = di_providers.Singleton(YtsmScheduler, appConfig)
    youtubeDLManager = di_providers.Singleton(YoutubeDlManager)
    providerManager = di_providers.Singleton(VideoProviderManager)
