import logging
import sys
from apscheduler.schedulers.background import BackgroundScheduler

instance: BackgroundScheduler = None


def initialize_scheduler():
    from .appconfig import settings
    global instance

    logger = logging.getLogger('scheduler')
    executors = {
        'default': {
            'type': 'threadpool',
            'max_workers': settings.getint('global', 'SchedulerConcurrency')
        }
    }
    job_defaults = {
        'misfire_grace_time': sys.maxsize
    }

    instance = BackgroundScheduler(logger=logger, executors=executors, job_defaults=job_defaults)
    instance.start()
