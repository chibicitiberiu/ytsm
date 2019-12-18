import re
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import Q

from YtManagerApp.models import Subscription, Video, SubscriptionFolder


def get_videos(user: User,
               sort_order: Optional[str],
               query: Optional[str] = None,
               subscription_id: Optional[int] = None,
               folder_id: Optional[int] = None,
               only_watched: Optional[bool] = None,
               only_downloaded: Optional[bool] = None,
               ):

    filter_args = []
    filter_kwargs = {
        'subscription__user': user
    }

    # Process query string - basically, we break it down into words,
    # and then search for the given text in the name, description, uploader name and subscription name
    if query is not None:
        for match in re.finditer(r'\w+', query):
            word = match[0]
            filter_args.append(Q(name__icontains=word)
                               | Q(description__icontains=word)
                               | Q(uploader_name__icontains=word)
                               | Q(subscription__name__icontains=word))

    # Subscription id
    if subscription_id is not None:
        filter_kwargs['subscription_id'] = subscription_id

    # Folder id
    if folder_id is not None:
        # Visit function - returns only the subscription IDs
        def visit(node):
            if isinstance(node, Subscription):
                return node.id
            return None
        filter_kwargs['subscription_id__in'] = SubscriptionFolder.traverse(folder_id, user, visit)

    # Only watched
    if only_watched is not None:
        filter_kwargs['watched'] = only_watched

    # Only downloaded
    # - not downloaded (False) -> is null (True)
    # - downloaded (True) -> is not null (False)
    if only_downloaded is not None:
        filter_kwargs['downloaded_path__isnull'] = not only_downloaded

    return Video.objects.filter(*filter_args, **filter_kwargs).order_by(sort_order)
