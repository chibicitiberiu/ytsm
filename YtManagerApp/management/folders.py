from YtManagerApp.models import SubscriptionFolder, Subscription
from typing import Callable, Union, Any, Optional
from django.contrib.auth.models import User
import logging
from django.db.models.functions import Lower


def traverse_tree(root_folder_id: Optional[int], user: User, visit_func: Callable[[Union[SubscriptionFolder, Subscription]], Any]):
    data_collected = []

    def collect(data):
        if data is not None:
            data_collected.append(data)

    # Visit root
    if root_folder_id is not None:
        root_folder = SubscriptionFolder.objects.get(id = root_folder_id)
        collect(visit_func(root_folder))

    queue = [root_folder_id]
    visited = []

    while len(queue) > 0:
        folder_id = queue.pop()

        if folder_id in visited:
            logging.error('Found folder tree cycle for folder id %d.', folder_id)
            continue
        visited.append(folder_id)

        for folder in SubscriptionFolder.objects.filter(parent_id=folder_id, user=user).order_by(Lower('name')):
            collect(visit_func(folder))
            queue.append(folder.id)

        for subscription in Subscription.objects.filter(parent_folder_id=folder_id, user=user).order_by(Lower('name')):
            collect(visit_func(subscription))

    return data_collected
