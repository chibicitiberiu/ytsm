import logging
import logging.handlers
import os

from django.conf import settings as dj_settings

from .management.appconfig import global_prefs
from .management.jobs.synchronize import schedule_synchronize_global
from .scheduler import initialize_scheduler
from django.db.utils import OperationalError

def __initialize_logger():
    log_dir = os.path.join(dj_settings.DATA_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "log.log"),
        maxBytes=1024 * 1024,
        backupCount=5
    )

    logging.basicConfig(
        level=dj_settings.LOG_LEVEL,
        format=dj_settings.LOG_FORMAT,
        handlers=[file_handler]
    )


def main():
    __initialize_logger()

    try:
        if global_prefs['hidden__initialized']:
            initialize_scheduler()
            schedule_synchronize_global()
    except OperationalError:
        # Settings table is not created when running migrate or makemigrations, so just don't do anything in this case.
        pass

    logging.info('Initialization complete.')
