import errno
import mimetypes
from threading import Lock

from apscheduler.triggers.cron import CronTrigger

from YtManagerApp.scheduler import scheduler
from YtManagerApp.management.appconfig import appconfig
from YtManagerApp.management.downloader import fetch_thumbnail, downloader_process_all, downloader_process_subscription
from YtManagerApp.models import *
from YtManagerApp.utils import youtube

from YtManagerApp.management import notification_manager

log = logging.getLogger('sync')
__lock = Lock()

_ENABLE_UPDATE_STATS = True


def __check_new_videos_sub(subscription: Subscription, yt_api: youtube.YoutubeAPI):
    # Get list of videos
    for item in yt_api.playlist_items(subscription.playlist_id):
        results = Video.objects.filter(video_id=item.resource_video_id, subscription=subscription)
        if len(results) == 0:
            log.info('New video for subscription %s: %s %s"', subscription, item.resource_video_id, item.title)
            Video.create(item, subscription)

    if _ENABLE_UPDATE_STATS:
        all_vids = Video.objects.filter(subscription=subscription)
        all_vids_ids = [video.video_id for video in all_vids]
        all_vids_dict = {v.video_id: v for v in all_vids}

        for yt_video in yt_api.videos(all_vids_ids, part='id,statistics'):
            video = all_vids_dict.get(yt_video.id)

            if yt_video.n_likes is not None \
                    and yt_video.n_dislikes is not None \
                    and yt_video.n_likes + yt_video.n_dislikes > 0:
                video.rating = yt_video.n_likes / (yt_video.n_likes + yt_video.n_dislikes)

            video.views = yt_video.n_views
            video.save()


def __detect_deleted(subscription: Subscription):

    user = subscription.user

    for video in Video.objects.filter(subscription=subscription, downloaded_path__isnull=False):
        found_video = False
        files = []
        try:
            files = list(video.get_files())
        except OSError as e:
            if e.errno != errno.ENOENT:
                log.error("Could not access path %s. Error: %s", video.downloaded_path, e)
                return

        # Try to find a valid video file
        for file in files:
            mime, _ = mimetypes.guess_type(file)
            if mime is not None and mime.startswith("video"):
                found_video = True

        # Video not found, we can safely assume that the video was deleted.
        if not found_video:
            log.info("Video %d was deleted! [%s %s]", video.id, video.video_id, video.name)
            # Clean up
            for file in files:
                try:
                    os.unlink(file)
                except OSError as e:
                    log.error("Could not delete redundant file %s. Error: %s", file, e)
            video.downloaded_path = None

            # Mark watched?
            if user.preferences['mark_deleted_as_watched']:
                video.watched = True

            video.save()


def __fetch_thumbnails_obj(iterable, obj_type, id_attr):
    for obj in iterable:
        if obj.icon_default.startswith("http"):
            obj.icon_default = fetch_thumbnail(obj.icon_default, obj_type, getattr(obj, id_attr), 'default')
        if obj.icon_best.startswith("http"):
            obj.icon_best = fetch_thumbnail(obj.icon_best, obj_type, getattr(obj, id_attr), 'best')
        obj.save()


def __fetch_thumbnails():
    log.info("Fetching subscription thumbnails... ")
    __fetch_thumbnails_obj(Subscription.objects.filter(icon_default__istartswith='http'), 'sub', 'playlist_id')
    __fetch_thumbnails_obj(Subscription.objects.filter(icon_best__istartswith='http'), 'sub', 'playlist_id')

    log.info("Fetching video thumbnails... ")
    __fetch_thumbnails_obj(Video.objects.filter(icon_default__istartswith='http'), 'video', 'video_id')
    __fetch_thumbnails_obj(Video.objects.filter(icon_best__istartswith='http'), 'video', 'video_id')


def synchronize():
    if not __lock.acquire(blocking=False):
        # Synchronize already running in another thread
        log.info("Synchronize already running in another thread")
        return

    try:
        log.info("Running scheduled synchronization... ")
        notification_manager.notify_status_update(f'Synchronization started for all subscriptions.')

        # Sync subscribed playlists/channels
        log.info("Sync - checking videos")
        yt_api = youtube.YoutubeAPI.build_public()
        for subscription in Subscription.objects.all():
            __check_new_videos_sub(subscription, yt_api)
            __detect_deleted(subscription)

        log.info("Sync - checking for videos to download")
        downloader_process_all()

        log.info("Sync - fetching missing thumbnails")
        __fetch_thumbnails()

        log.info("Synchronization finished.")
        notification_manager.notify_status_update(f'Synchronization finished for all subscriptions.')

    finally:
        __lock.release()


def synchronize_subscription(subscription: Subscription):
    __lock.acquire()
    try:
        log.info("Running synchronization for single subscription %d [%s]", subscription.id, subscription.name)
        notification_manager.notify_status_update(f'Synchronization started for subscription <strong>{subscription.name}</strong>.')

        yt_api = youtube.YoutubeAPI.build_public()

        log.info("Sync - checking videos")
        __check_new_videos_sub(subscription, yt_api)
        __detect_deleted(subscription)

        log.info("Sync - checking for videos to download")
        downloader_process_subscription(subscription)

        log.info("Sync - fetching missing thumbnails")
        __fetch_thumbnails()

        log.info("Synchronization finished for subscription %d [%s].", subscription.id, subscription.name)
        notification_manager.notify_status_update(f'Synchronization finished for subscription <strong>{subscription.name}</strong>.')

    finally:
        __lock.release()


__global_sync_job = None


def schedule_synchronize_global():
    global __global_sync_job

    trigger = CronTrigger.from_crontab(appconfig.sync_schedule)

    if __global_sync_job is None:
        trigger = CronTrigger.from_crontab(appconfig.sync_schedule)
        __global_sync_job = scheduler.add_job(synchronize, trigger, max_instances=1, coalesce=True)

    else:
        __global_sync_job.reschedule(trigger, max_instances=1, coalesce=True)

    log.info('Scheduled synchronize job job=%s', __global_sync_job.id)


def schedule_synchronize_now():
    job = scheduler.add_job(synchronize, max_instances=1, coalesce=True)
    log.info('Scheduled synchronize now job job=%s', job.id)


def schedule_synchronize_now_subscription(subscription: Subscription):
    job = scheduler.add_job(synchronize_subscription, args=[subscription])
    log.info('Scheduled synchronize subscription job subscription=(%s), job=%s', subscription, job.id)
