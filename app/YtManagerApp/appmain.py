import logging
import logging.handlers
import os
import sys

from django.conf import settings as dj_settings

from .management.appconfig import appconfig
from .management.jobs.synchronize import schedule_synchronize_global
from .scheduler import initialize_scheduler
from django.db.utils import OperationalError


def __initialize_logger():
    log_dir = os.path.join(dj_settings.DATA_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    handlers = []

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "log.log"),
        maxBytes=1024 * 1024,
        backupCount=5
    )
    handlers.append(file_handler)

    if dj_settings.DEBUG:
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        handlers.append(console_handler)

    logging.basicConfig(
        level=dj_settings.LOG_LEVEL,
        format=dj_settings.LOG_FORMAT,
        handlers=handlers
    )


def main():
    __initialize_logger()

    try:
        if appconfig.initialized:
            initialize_scheduler()
            schedule_synchronize_global()
    except OperationalError:
        # Settings table is not created when running migrate or makemigrations, so just don't do anything in this case.
        pass

    logging.info('Initialization complete.')
