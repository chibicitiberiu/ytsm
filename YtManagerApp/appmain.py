from .appconfig import initialize_app_config
from .scheduler import initialize_scheduler
from .management.jobs.synchronize import schedule_synchronize
import logging


def main():
    initialize_app_config()
    initialize_scheduler()
    schedule_synchronize()
    logging.info('Initialization complete.')
