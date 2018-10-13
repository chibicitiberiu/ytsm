import logging
from apscheduler.schedulers.background import BackgroundScheduler

from .appconfig import settings

instance: BackgroundScheduler = None


def initialize_scheduler():
    global instance
    logger = logging.getLogger('scheduler')
    executors = {
        'default': {
            'type': 'threadpool',
            'max_workers': settings.getint('global', 'SchedulerConcurrency')
        }
    }

    instance = BackgroundScheduler(logger=logger, executors=executors)
    instance.start()
