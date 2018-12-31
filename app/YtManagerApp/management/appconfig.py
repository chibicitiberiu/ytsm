from dynamic_preferences.registries import global_preferences_registry
from YtManagerApp.dynamic_preferences_registry import Initialized, YouTubeAPIKey, AllowRegistrations, SyncSchedule, SchedulerConcurrency


class AppConfig(object):
    # Properties
    props = {
        'initialized': Initialized,
        'youtube_api_key': YouTubeAPIKey,
        'allow_registrations': AllowRegistrations,
        'sync_schedule': SyncSchedule,
        'concurrency': SchedulerConcurrency
    }

    # Init
    def __init__(self, pref_manager):
        self.__pref_manager = pref_manager

    def __getattr__(self, item):
        prop_class = AppConfig.props[item]
        prop_full_name = prop_class.section.name + "__" + prop_class.name
        return self.__pref_manager[prop_full_name]

    def __setattr__(self, key, value):
        if key in AppConfig.props:
            prop_class = AppConfig.props[key]
            prop_full_name = prop_class.section.name + "__" + prop_class.name
            self.__pref_manager[prop_full_name] = value
        else:
            super().__setattr__(key, value)

    def for_sub(self, subscription, pref: str):
        value = getattr(subscription, pref)
        if value is None:
            value = subscription.user.preferences[pref]

        return value


global_prefs = global_preferences_registry.manager()
appconfig = AppConfig(global_prefs)
