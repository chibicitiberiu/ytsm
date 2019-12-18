import datetime
import logging
import traceback
from typing import Type, Union, Optional

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.interval import IntervalTrigger
from django.contrib.auth.models import User

from YtManagerApp.services.appconfig import AppConfig
from YtManagerApp.models import JobExecution, JOB_STATES_MAP
from YtManagerApp.services.scheduler.job import Job
from YtManagerApp.services.scheduler.jobs.youtubedl_update_job import YouTubeDLUpdateJob


class YtsmScheduler(object):

    def __init__(self, app_config: AppConfig):
        self._ap_scheduler = BackgroundScheduler()
        self._app_config = app_config

    def initialize(self):
        # set state of existing jobs as "interrupted"
        JobExecution.objects\
            .filter(status=JOB_STATES_MAP['running'])\
            .update(status=JOB_STATES_MAP['interrupted'])

        self._configure_scheduler()
        self._ap_scheduler.start()
        self._schedule_main_jobs()

    def _schedule_main_jobs(self):
        self.add_job(YouTubeDLUpdateJob, trigger=IntervalTrigger(days=1))

    def _configure_scheduler(self):
        logger = logging.getLogger('scheduler')
        executors = {
            'default': {
                'type': 'threadpool',
                'max_workers': self._app_config.concurrency
            }
        }
        job_defaults = {
            'misfire_grace_time': 60 * 60 * 24 * 365  # 1 year
        }
        self._ap_scheduler.configure(logger=logger, executors=executors, job_defaults=job_defaults)

    def _run_job(self, job_class: Type[Job], user: Optional[User], args: Union[tuple, list]):

        job_execution = JobExecution(user=user, status=JOB_STATES_MAP['running'])
        job_execution.save()
        job_instance = job_class(job_execution, *args)

        # update description
        job_execution.description = job_instance.get_description()
        job_execution.save()

        try:
            job_instance.run()
            job_execution.status = JOB_STATES_MAP['finished']

        except Exception as ex:
            job_instance.log.critical("Job failed with exception: %s", traceback.format_exc())
            job_instance.usr_err(job_instance.name + " operation failed: " + str(ex))
            job_execution.status = JOB_STATES_MAP['failed']

        finally:
            job_execution.end_date = datetime.datetime.now(tz=pytz.UTC)
            job_execution.save()

    def add_job(self, job_class: Type[Job], trigger: Union[str, BaseTrigger] = None,
                args: Union[list, tuple] = None,
                user: Optional[User] = None,
                **kwargs):
        if args is None:
            args = []

        return self._ap_scheduler.add_job(YtsmScheduler._run_job, trigger=trigger, args=[self, job_class, user, args],
                                          **kwargs)
