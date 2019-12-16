import logging
from abc import abstractmethod
from typing import Optional

from YtManagerApp.models import JOB_MESSAGE_LEVELS_MAP, JobMessage
from .progress_tracker import ProgressTracker


class Job(object):
    name = 'GenericJob'

    """
    Base class for jobs running in the scheduler.
    """

    def __init__(self, job_execution, *_):
        self.job_execution = job_execution
        self.log = logging.getLogger(self.name)
        self.__progress_tracker = ProgressTracker(listener=Job.__on_progress,
                                                  listener_args=[self])

    @abstractmethod
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
    @abstractmethod
    def run(self):
        pass
