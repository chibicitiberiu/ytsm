from .appconfig import initialize_config
from .scheduler import initialize_scheduler
from .management import setup_synchronization_job
import logging


def main():
    initialize_config()
    initialize_scheduler()
    setup_synchronization_job()
    logging.info('Initialization complete.')
