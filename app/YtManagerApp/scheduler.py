import logging

from apscheduler.schedulers.background import BackgroundScheduler

from YtManagerApp.management.appconfig import appconfig

scheduler: BackgroundScheduler = None


def initialize_scheduler():
    global scheduler

    logger = logging.getLogger('scheduler')
    executors = {
        'default': {
            'type': 'threadpool',
            'max_workers': appconfig.concurrency
        }
    }
    job_defaults = {
        'misfire_grace_time': 60 * 60 * 24 * 365        # 1 year
    }

    scheduler = BackgroundScheduler(logger=logger, executors=executors, job_defaults=job_defaults)
    scheduler.start()
