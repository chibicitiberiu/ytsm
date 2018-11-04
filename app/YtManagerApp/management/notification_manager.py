from django.contrib.auth.models import User
from typing import Dict, Deque, Any, Optional
from collections import deque
from datetime import datetime, timedelta
from YtManagerApp.utils.algorithms import bisect_left
from threading import Lock

# Clients will request updates at most every few seconds, so a retention period of 60 seconds should be more than
# enough. I gave it 15 minutes so that if for some reason the connection fails (internet drops) and then comes back a
# few minutes later, the client will still get the updates
__RETENTION_PERIOD = 15 * 60
__NOTIFICATIONS: Deque[Dict] = deque()
__NEXT_ID = 0
__LOCK = Lock()


# Messages enum
class Messages:
    STATUS_UPDATE = 'st-up'
    STATUS_OPERATION_PROGRESS = 'st-op-prog'
    STATUS_OPERATION_END = 'st-op-end'


def __add_notification(message, user: User=None, **kwargs):
    global __NEXT_ID

    __LOCK.acquire()

    try:
        # add notification
        notification = {
            'time': datetime.now(),
            'msg': message,
            'id': __NEXT_ID,
            'uid': user and user.id,
        }
        notification.update(kwargs)
        __NOTIFICATIONS.append(notification)
        __NEXT_ID += 1

        # trim old notifications
        oldest = __NOTIFICATIONS[0]
        while len(__NOTIFICATIONS) > 0 and oldest['time'] + timedelta(seconds=__RETENTION_PERIOD) < datetime.now():
            __NOTIFICATIONS.popleft()
            oldest = __NOTIFICATIONS[0]

    finally:
        __LOCK.release()


def get_notifications(user: User, last_received_id: Optional[int]):

    __LOCK.acquire()

    try:
        first_index = 0
        if last_received_id is not None:
            first_index = bisect_left(__NOTIFICATIONS,
                                 {'id': last_received_id},
                                 key=lambda item: item['id'])

        for i in range(first_index, len(__NOTIFICATIONS)):
            item = __NOTIFICATIONS[i]
            if item['uid'] is None or item['uid'] == user.id:
                yield item

    finally:
        __LOCK.release()


def get_current_notification_id():
    return __NEXT_ID


def notify_status_update(status_message: str, user: User=None):
    __add_notification(Messages.STATUS_UPDATE,
                       user=user,
                       status=status_message)


def notify_status_operation_progress(op_id: Any, status_message: str, progress_percent: float, user: User=None):
    __add_notification(Messages.STATUS_OPERATION_PROGRESS,
                       user=user,
                       operation=op_id,
                       status=status_message,
                       progress=progress_percent)


def notify_status_operation_ended(op_id: Any, status_message: str, user: User=None):
    __add_notification(Messages.STATUS_OPERATION_END,
                       user=user,
                       operation=op_id,
                       status=status_message)
