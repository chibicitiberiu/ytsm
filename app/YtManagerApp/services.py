import dependency_injector.containers as containers
import dependency_injector.providers as providers
from dynamic_preferences.registries import global_preferences_registry
from YtManagerApp.management.appconfig import AppConfig
from YtManagerApp.management.download_manager import DownloadManager
from YtManagerApp.management.subscription_manager import SubscriptionManager
from YtManagerApp.management.video_manager import VideoManager
from YtManagerApp.management.video_provider_manager import VideoProviderManager
from YtManagerApp.management.youtube_dl_manager import YoutubeDlManager
from YtManagerApp.scheduler.scheduler import YtsmScheduler


class VideoProviders(containers.DeclarativeContainer):
    from YtManagerApp.providers.ytapi_video_provider import YouTubeApiVideoProvider
    ytApiProvider = providers.Factory(YouTubeApiVideoProvider)


class Services(containers.DeclarativeContainer):
    globalPreferencesRegistry = providers.Object(global_preferences_registry.manager())
    appConfig = providers.Singleton(AppConfig, globalPreferencesRegistry)
    scheduler = providers.Singleton(YtsmScheduler, appConfig)
    youtubeDLManager = providers.Singleton(YoutubeDlManager)
    videoManager = providers.Singleton(VideoManager)
    videoProviderManager = providers.Singleton(VideoProviderManager, [VideoProviders.ytApiProvider()])
    subscriptionManager = providers.Singleton(SubscriptionManager)
    downloadManager = providers.Singleton(DownloadManager)
