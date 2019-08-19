import datetime
import logging
import traceback
from typing import Type, Union, Optional, Callable, List, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.base import BaseTrigger
from django.contrib.auth.models import User

from YtManagerApp.management.appconfig import appconfig
from YtManagerApp.models import JobExecution, JobMessage, JOB_STATES_MAP, JOB_MESSAGE_LEVELS_MAP


class ProgressTracker(object):
    """
    Class which helps keep track of complex operation progress.
    """

    def __init__(self, total_steps: float = 100, initial_steps: float = 0,
                 listener: Callable[[float, str], None] = None,
                 listener_args: List[Any] = None,
                 parent: Optional["ProgressTracker"] = None):
        """
        Constructor
        :param total_steps: Total number of steps required by this operation
        :param initial_steps: Starting steps
        :param parent: Parent progress tracker
        :param listener: Callable which is called when any progress happens
        """

        self.total_steps = total_steps
        self.steps = initial_steps

        self.__subtask: ProgressTracker = None
        self.__subtask_steps = 0

        self.__parent = parent
        self.__listener = listener
        self.__listener_args = listener_args or []

    def __on_progress(self, progress_msg):
        if self.__listener is not None:
            self.__listener(*self.__listener_args, self.compute_progress(), progress_msg)

        if self.__parent is not None:
            self.__parent.__on_progress(progress_msg)

    def advance(self, steps: float = 1, progress_msg: str = ''):
        """
        Advances a number of steps.
        :param steps: Number of steps to advance
        :param progress_msg: A message which will be passed to a listener
        :return:
        """

        # We can assume previous subtask is now completed
        if self.__subtask is not None:
            self.steps += self.__subtask_steps
            self.__subtask = None

        self.steps += steps
        self.__on_progress(progress_msg)

    def subtask(self, steps: float = 1, subtask_total_steps: float = 100, subtask_initial_steps: float = 0):
        """
        Creates a 'subtask' which has its own progress, which will be used in the calculation of the final progress.
        :param steps: Number of steps the subtask is 'worth'
        :param subtask_total_steps: Total number of steps for subtask
        :param subtask_initial_steps: Initial steps for subtask
        :return: ProgressTracker for subtask
        """

        # We can assume previous subtask is now completed
        if self.__subtask is not None:
            self.steps += self.__subtask_steps

        self.__subtask = ProgressTracker(total_steps=subtask_total_steps,
                                         initial_steps=subtask_initial_steps,
                                         parent=self)
        self.__subtask_steps = steps

        return self.__subtask

    def compute_progress(self):
        """
        Calculates final progress value in percent.
        :return: value in [0,1] interval representing progress
        """
        base = float(self.steps) / self.total_steps
        if self.__subtask is not None:
            base += self.__subtask.compute_progress() * self.__subtask_steps / self.total_steps

        return min(base, 1.0)


class Job(object):
    name = 'GenericJob'

    """
    Base class for jobs running in the scheduler.
    """

    def __init__(self, job_execution, *args):
        self.job_execution = job_execution
        self.log = logging.getLogger(self.name)
        self.__progress_tracker = ProgressTracker(listener=Job.__on_progress,
                                                  listener_args=[self])

    def get_description(self) -> str:
        """
        Gets a user friendly description of this job.
        Should be overriden in job classes.
        :return:
        """
        return "Running job..."

    #
    # progress tracking
    #

    def __on_progress(self, percent: float, message: str):
        self.usr_log(message, progress=percent)

    def set_total_steps(self, steps: float):
        """
        Sets the total number of work steps this task has. This is used for tracking progress.
        Should be overriden in job classes.
        :return:
        """
        self.__progress_tracker.total_steps = steps

    def progress_advance(self, steps: float = 1, progress_msg: str = ''):
        """
        Advances a number of steps.
        :param steps: Number of steps to advance
        :param progress_msg: A message which will be passed to a listener
        :return:
        """
        self.__progress_tracker.advance(steps, progress_msg)

    def create_subtask(self, steps: float = 1, subtask_total_steps: float = 100, subtask_initial_steps: float = 0):
        """
        Creates a 'subtask' which has its own progress, which will be used in the calculation of the final progress.
        :param steps: Number of steps the subtask is 'worth'
        :param subtask_total_steps: Total number of steps for subtask
        :param subtask_initial_steps: Initial steps for subtask
        :return: ProgressTracker for subtask
        """
        return self.__progress_tracker.subtask(steps, subtask_total_steps, subtask_initial_steps)

    #
    # user log messages
    #

    def usr_log(self, message, progress: Optional[float] = None, level: int = JOB_MESSAGE_LEVELS_MAP['normal'],
                suppress_notification: bool = False):
        """
        Creates a new log message which will be shown on the user interface.
        Progress can also be updated using this method.
        :param message: A message to be displayed to the user
        :param progress: Progress percentage in [0,1] interval
        :param level: Log level (normal, warning, error)
        :param suppress_notification: If set to true, a notification will not displayed to the user, but it will
        appear in the system logs.
        :return:
        """

        message = JobMessage(job=self.job_execution,
                             progress=progress,
                             message=message,
                             level=level,
                             suppress_notification=suppress_notification)
        message.save()

    def usr_warn(self, message, progress: Optional[float] = None, suppress_notification: bool = False):
        """
        Creates a new warning message which will be shown on the user interface.
        Progress can also be updated using this method.
        :param message: A message to be displayed to the user
        :param progress: Progress percentage in [0,1] interval
        :param suppress_notification: If set to true, a notification will not displayed to the user, but it will
        appear in the system logs.
        :return:
        """
        self.usr_log(message, progress, JOB_MESSAGE_LEVELS_MAP['warning'], suppress_notification)

    def usr_err(self, message, progress: Optional[float] = None, suppress_notification: bool = False):
        """
        Creates a new error message which will be shown on the user interface.
        Progress can also be updated using this method.
        :param message: A message to be displayed to the user
        :param progress: Progress percentage in [0,1] interval
        :param suppress_notification: If set to true, a notification will not displayed to the user, but it will
        appear in the system logs.
        :return:
        """
        self.usr_log(message, progress, JOB_MESSAGE_LEVELS_MAP['error'], suppress_notification)

    #
    # main run method
    #
    def run(self):
        pass


class YtsmScheduler(object):

    def __init__(self):
        self._apscheduler = BackgroundScheduler()

    def initialize(self):
        # set state of existing jobs as "interrupted"
        JobExecution.objects\
            .filter(status=JOB_STATES_MAP['running'])\
            .update(status=JOB_STATES_MAP['interrupted'])

        self._configure_scheduler()
        self._apscheduler.start()

    def _configure_scheduler(self):
        logger = logging.getLogger('scheduler')
        executors = {
            'default': {
                'type': 'threadpool',
                'max_workers': appconfig.concurrency
            }
        }
        job_defaults = {
            'misfire_grace_time': 60 * 60 * 24 * 365  # 1 year
        }
        self._apscheduler.configure(logger=logger, executors=executors, job_defaults=job_defaults)

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
            job_execution.end_date = datetime.datetime.now()
            job_execution.save()

    def add_job(self, job_class: Type[Job], trigger: Union[str, BaseTrigger] = None,
                args: Union[list, tuple] = None,
                user: Optional[User] = None,
                **kwargs):
        if args is None:
            args = []

        return self._apscheduler.add_job(YtsmScheduler._run_job, trigger=trigger, args=[self, job_class, user, args],
                                         **kwargs)


scheduler = YtsmScheduler()
