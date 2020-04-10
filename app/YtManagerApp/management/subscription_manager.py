import errno
import itertools
import mimetypes
import os
from threading import Lock
from typing import Optional, List, Union

from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.db.models import Max

from YtManagerApp.models import *
from YtManagerApp.providers.video_provider import VideoProvider, InvalidURLError
from YtManagerApp.scheduler.job import Job
from YtManagerApp.utils.algorithms import group_by

_ENABLE_UPDATE_STATS = True


class SynchronizeJob(Job):
    name = "SynchronizeJob"
    __lock = Lock()
    running = False
    __global_sync_job = None

    def __init__(self, job_execution, subscription: Optional[Subscription] = None):
        super().__init__(job_execution)
        self.__subscription: Optional[Subscription] = subscription
        self.__new_vids: List[Video] = []

    def get_description(self):
        if self.__subscription is not None:
            return "Running synchronization for subscription " + self.__subscription.name
        return "Running synchronization..."

    def get_subscription_list(self):
        if self.__subscription is not None:
            return [self.__subscription]
        return Subscription.objects.all()

    def get_videos_list(self, subs):
        return Video.objects.filter(subscription__in=subs)

    def run(self):
        from YtManagerApp.services import Services

        self.__lock.acquire(blocking=True)
        SynchronizeJob.running = True
        try:
            self.log.info(self.get_description())

            # Build list of work items
            work_subs = self.get_subscription_list()
            work_vids = self.get_videos_list(work_subs)

            self.set_total_steps(len(work_subs) + len(work_vids))

            # Remove the 'new' flag
            work_vids.update(new=False)

            # Process subscriptions
            for sub in work_subs:
                self.progress_advance(1, "Synchronizing subscription " + sub.name)
                self.check_new_videos(sub)
                self.fetch_missing_thumbnails(sub)

            # Add new videos to progress calculation
            self.set_total_steps(len(work_subs) + len(work_vids) + len(self.__new_vids))

            # Group videos by provider
            all_videos = itertools.chain(work_vids, self.__new_vids)
            all_videos_by_provider = group_by(all_videos, lambda x: x.subscription.provider_id)

            for provider_id, videos in all_videos_by_provider.items():
                provider: VideoProvider = Services.videoProviderManager().get(provider_id)
                if _ENABLE_UPDATE_STATS:
                    provider.update_videos(videos, update_statistics=True)

                for video in videos:
                    self.progress_advance(1, "Updating video " + video.name)
                    self.check_video_deleted(video)
                    self.fetch_missing_thumbnails(video)

            # Start downloading videos
            for sub in work_subs:
                Services.downloadManager().process_subscription(sub)

        finally:
            SynchronizeJob.running = False
            self.__lock.release()

    def check_new_videos(self, sub: Subscription):
        from YtManagerApp.services import Services
        provider: VideoProvider = Services.videoProviderManager().get(sub)

        playlist_videos = provider.fetch_videos(sub)
        if sub.rewrite_playlist_indices:
            playlist_videos = sorted(playlist_videos, key=lambda x: x.publish_date)
        else:
            playlist_videos = sorted(playlist_videos, key=lambda x: x.playlist_index)

        for item in playlist_videos:
            results = Video.objects.filter(video_id=item.video_id, subscription=sub)

            if not results.exists():
                self.log.info('New video for subscription %s: %s %s"', sub, item.video_id, item.name)

                # fix playlist index if necessary
                if sub.rewrite_playlist_indices or Video.objects.filter(subscription=sub,
                                                                        playlist_index=item.playlist_index).exists():
                    highest = Video.objects.filter(subscription=sub).aggregate(Max('playlist_index'))[
                        'playlist_index__max']
                    item.playlist_index = 1 + (highest or -1)

                item.save()
                self.__new_vids.append(item)

    def fetch_missing_thumbnails(self, obj: Union[Subscription, Video]):
        from YtManagerApp.services import Services
        if obj.thumbnail.startswith("http"):
            if isinstance(obj, Subscription):
                obj.thumbnail = Services.downloadManager().fetch_thumbnail(obj.thumbnail, 'sub', obj.playlist_id,
                                                                           settings.THUMBNAIL_SIZE_SUBSCRIPTION)
            elif isinstance(obj, Video):
                obj.thumbnail = Services.downloadManager().fetch_thumbnail(obj.thumbnail, 'video', obj.video_id,
                                                                           settings.THUMBNAIL_SIZE_VIDEO)
            obj.save()

    def check_video_deleted(self, video: Video):
        if video.downloaded_path is not None:
            files = []
            try:
                files = list(video.get_files())
            except OSError as e:
                if e.errno != errno.ENOENT:
                    self.log.error("Could not access path %s. Error: %s", video.downloaded_path, e)
                    self.usr_err(f"Could not access path {video.downloaded_path}: {e}", suppress_notification=True)
                    return

            # Try to find a valid video file
            found_video = False
            for file in files:
                mime, _ = mimetypes.guess_type(file)
                if mime is not None and mime.startswith("video"):
                    found_video = True

            # Video not found, we can safely assume that the video was deleted.
            if not found_video:
                self.log.info("Video %d was deleted! [%s %s]", video.id, video.video_id, video.name)
                # Clean up
                for file in files:
                    try:
                        os.unlink(file)
                    except OSError as e:
                        self.log.error("Could not delete redundant file %s. Error: %s", file, e)
                        self.usr_err(f"Could not delete redundant file {file}: {e}", suppress_notification=True)
                video.downloaded_path = None

                # Mark watched?
                user = video.subscription.user
                if user.preferences['mark_deleted_as_watched']:
                    video.watched = True

                video.save()

    def update_video_stats(self, video: Video, yt_video):
        if yt_video.n_likes is not None \
                and yt_video.n_dislikes is not None \
                and yt_video.n_likes + yt_video.n_dislikes > 0:
            video.rating = yt_video.n_likes / (yt_video.n_likes + yt_video.n_dislikes)

        video.views = yt_video.n_views
        video.save()


class SubscriptionImporterJob(Job):
    def __init__(self, job_execution, urls: List[str],
                 parent_folder: SubscriptionFolder,
                 auto_download: bool,
                 download_limit: int,
                 download_order: str,
                 automatically_delete_watched: bool):

        super().__init__(job_execution)
        self._urls = urls
        self._parent_folder = parent_folder
        self._auto_download = auto_download
        self._download_limit = download_limit
        self._download_order = download_order
        self._automatically_delete_watched = automatically_delete_watched

    def get_description(self):
        return f"Importing {len(self._urls)} subscriptions..."

    def run(self):
        from YtManagerApp.services import Services
        self.set_total_steps(len(self._urls))
        for url in self._urls:
            try:
                self.progress_advance(progress_msg=url)
                sub: Subscription = Services.videoProviderManager().fetch_subscription(url)
                sub.parent_folder = self._parent_folder
                sub.auto_download = self._auto_download
                sub.download_limit = self._download_limit
                sub.download_order = self._download_order
                sub.automatically_delete_watched = self._automatically_delete_watched
                sub.save()
            except InvalidURLError as e:
                self.log.error("Error importing URL %s: %s", url, e)
            except ValueError as e:
                self.log.error("Error importing URL %s: %s", url, e)


class SubscriptionManager(object):
    def __init__(self):
        self.__global_sync_job = None

    def synchronize(self, sub: Subscription):
        from YtManagerApp.services import Services
        Services.scheduler().add_job(SynchronizeJob, args=[sub])

    def synchronize_all(self):
        from YtManagerApp.services import Services
        Services.scheduler().add_job(SynchronizeJob, max_instances=1, coalesce=True)

    def schedule_global_synchronize_job(self):
        from YtManagerApp.services import Services
        trigger = CronTrigger.from_crontab(Services.appConfig().sync_schedule)

        if self.__global_sync_job is None:
            trigger = CronTrigger.from_crontab(Services.appConfig().sync_schedule)
            SynchronizeJob.__global_sync_job = Services.scheduler().add_job(SynchronizeJob, trigger, max_instances=1,
                                                                            coalesce=True)

        else:
            self.__global_sync_job.reschedule(trigger, max_instances=1, coalesce=True)

    def import_multiple(self, urls: List[str],
                        parent_folder: SubscriptionFolder,
                        auto_download: bool,
                        download_limit: int,
                        download_order: str,
                        automatically_delete_watched: bool):
        from YtManagerApp.services import Services
        Services.scheduler().add_job(SubscriptionImporterJob, args=[urls, parent_folder, auto_download, download_limit,
                                                                    download_order, automatically_delete_watched])
