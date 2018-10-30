import logging
import sys
from apscheduler.schedulers.background import BackgroundScheduler

scheduler: BackgroundScheduler = None


def initialize_scheduler():
    from .appconfig import settings
    global scheduler

    logger = logging.getLogger('scheduler')
    executors = {
        'default': {
            'type': 'threadpool',
            'max_workers': settings.getint('global', 'SchedulerConcurrency')
        }
    }
    job_defaults = {
        'misfire_grace_time': 60 * 60 * 24 * 365        # 1 year
    }

    scheduler = BackgroundScheduler(logger=logger, executors=executors, job_defaults=job_defaults)
    scheduler.start()
