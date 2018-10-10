import logging
from apscheduler.schedulers.background import BackgroundScheduler

from .appconfig import instance as app_config

instance: BackgroundScheduler = None


def initialize_scheduler():
    global instance
    logger = logging.getLogger('scheduler')
    executors = {
        'default': {
            'type': 'threadpool',
            'max_workers': int(app_config.get('global', 'SchedulerConcurrency'))
        }
    }

    instance = BackgroundScheduler(logger=logger, executors=executors)
    instance.start()
