import logging
import os
import os.path
from collections import ChainMap
from configparser import ConfigParser
from shutil import copyfile
from typing import Optional, Any

from django.conf import settings as dj_settings
from django.contrib.auth.models import User

from .models import UserSettings, Subscription
from .utils.extended_interpolation_with_env import ExtendedInterpolatorWithEnv


class AppSettings(ConfigParser):
    _DEFAULT_INTERPOLATION = ExtendedInterpolatorWithEnv()

    def __init__(self, *args, **kwargs):
        super().__init__(allow_no_value=True, *args, **kwargs)

    def initialize(self):
        self.read([dj_settings.DEFAULTS_FILE, dj_settings.CONFIG_FILE])

    def save(self):
        if os.path.exists(dj_settings.CONFIG_FILE):
            # Create a backup
            copyfile(dj_settings.CONFIG_FILE, dj_settings.CONFIG_FILE + ".backup")
        else:
            # Ensure directory exists
            settings_dir = os.path.dirname(dj_settings.CONFIG_FILE)
            os.makedirs(settings_dir, exist_ok=True)

        with open(dj_settings.CONFIG_FILE, 'w') as f:
            self.write(f)

    def __get_combined_dict(self, vars: Optional[Any], sub: Optional[Subscription], user: Optional[User]) -> ChainMap:
        vars_dict = {}
        sub_overloads_dict = {}
        user_settings_dict = {}

        if vars is not None:
            vars_dict = vars

        if sub is not None:
            sub_overloads_dict = sub.get_overloads_dict()

        if user is not None:
            user_settings = UserSettings.find_by_user(user)
            if user_settings is not None:
                user_settings_dict = user_settings.to_dict()

        return ChainMap(vars_dict, sub_overloads_dict, user_settings_dict)

    def get_user(self, user: User, section: str, option: Any, vars=None, fallback=object()) -> str:
        return super().get(section, option,
                           fallback=fallback,
                           vars=self.__get_combined_dict(vars, None, user))

    def getboolean_user(self, user: User, section: str, option: Any, vars=None, fallback=object()) -> bool:
        return super().getboolean(section, option,
                                  fallback=fallback,
                                  vars=self.__get_combined_dict(vars, None, user))

    def getint_user(self, user: User, section: str, option: Any, vars=None, fallback=object()) -> int:
        return super().getint(section, option,
                              fallback=fallback,
                              vars=self.__get_combined_dict(vars, None, user))

    def getfloat_user(self, user: User, section: str, option: Any, vars=None, fallback=object()) -> float:
        return super().getfloat(section, option,
                                fallback=fallback,
                                vars=self.__get_combined_dict(vars, None, user))

    def get_sub(self, sub: Subscription, section: str, option: Any, vars=None, fallback=object()) -> str:
        return super().get(section, option,
                           fallback=fallback,
                           vars=self.__get_combined_dict(vars, sub, sub.user))

    def getboolean_sub(self, sub: Subscription, section: str, option: Any, vars=None, fallback=object()) -> bool:
        return super().getboolean(section, option,
                                  fallback=fallback,
                                  vars=self.__get_combined_dict(vars, sub, sub.user))

    def getint_sub(self, sub: Subscription, section: str, option: Any, vars=None, fallback=object()) -> int:
        return super().getint(section, option,
                              fallback=fallback,
                              vars=self.__get_combined_dict(vars, sub, sub.user))

    def getfloat_sub(self, sub: Subscription, section: str, option: Any, vars=None, fallback=object()) -> float:
        return super().getfloat(section, option,
                                fallback=fallback,
                                vars=self.__get_combined_dict(vars, sub, sub.user))


settings = AppSettings()


def initialize_app_config():
    settings.initialize()
    __initialize_logger()
    logging.info('Application started!')


def __initialize_logger():
    log_dir = os.path.dirname(dj_settings.LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        filename=dj_settings.LOG_FILE,
        level=dj_settings.LOG_LEVEL,
        format=dj_settings.LOG_FORMAT)
