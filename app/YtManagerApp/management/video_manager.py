import os
import re
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import Q

from YtManagerApp.models import Subscription, Video, SubscriptionFolder
from YtManagerApp.scheduler.job import Job


class DeleteVideoJob(Job):
    """
    Deletes a video's files.
    """
    name = "DeleteVideoJob"

    def __init__(self, job_execution, video: Video):
        super().__init__(job_execution)
        self._video = video

    def get_description(self):
        return f"Deleting video {self._video}"

    def run(self):
        count = 0

        try:
            for file in self._video.get_files():
                self.log.info("Deleting file %s", file)
                count += 1
                try:
                    os.unlink(file)
                except OSError as e:
                    self.log.error("Failed to delete file %s: Error: %s", file, e)

        except OSError as e:
            self.log.error("Failed to delete video %d [%s %s]. Error: %s", self._video.id,
                           self._video.video_id, self._video.name, e)

        self._video.downloaded_path = None
        self._video.save()

        self.log.info('Deleted video %d successfully! (%d files) [%s %s]', self._video.id, count,
                      self._video.video_id, self._video.name)


class VideoManager(object):
    def __init__(self):
        pass

    def get_videos(self,
                   user: User,
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

    def delete_files(self, video: Video):
        from YtManagerApp.services import Services
        Services.scheduler().add_job(DeleteVideoJob, args=[video])

    def download(self, video: Video, attempt: int = 1):
        from YtManagerApp.services import Services
        Services.downloadManager().download_video(video, attempt)

    def mark_watched(self, video: Video):
        from YtManagerApp.services import Services
        video.watched = True
        video.save()
        if video.downloaded_path is not None:
            if Services.appConfig().for_sub(video.subscription, 'automatically_delete_watched'):
                self.delete_files(video)
                Services.subscriptionManager().synchronize(video.subscription)

    def mark_unwatched(self, video: Video):
        from YtManagerApp.services import Services
        video.watched = False
        video.save()
        Services.subscriptionManager().synchronize(video.subscription)
