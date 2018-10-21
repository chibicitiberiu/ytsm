from YtManagerApp.models import Subscription, Video, SubscriptionFolder
from YtManagerApp.utils.youtube import YoutubePlaylistItem
from typing import Optional
import re
from django.db.models import Q
from django.contrib.auth.models import User


def create_video(yt_video: YoutubePlaylistItem, subscription: Subscription):
    video = Video()
    video.video_id = yt_video.getVideoId()
    video.name = yt_video.getTitle()
    video.description = yt_video.getDescription()
    video.watched = False
    video.downloaded_path = None
    video.subscription = subscription
    video.playlist_index = yt_video.getPlaylistIndex()
    video.publish_date = yt_video.getPublishDate()
    video.icon_default = yt_video.getDefaultThumbnailUrl()
    video.icon_best = yt_video.getBestThumbnailUrl()
    video.save()
    return video


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
