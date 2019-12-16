from typing import Callable, List, Any, Optional


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
