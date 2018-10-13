import logging

from apscheduler.triggers.cron import CronTrigger

from YtManagerApp.appconfig import settings
from YtManagerApp.management.downloader import fetch_thumbnail, downloader_process_all
from YtManagerApp.management.videos import create_video
from YtManagerApp.models import *
from YtManagerApp import scheduler
from YtManagerApp.utils.youtube import YoutubeAPI

log = logging.getLogger('sync')


def __synchronize_sub(subscription: Subscription, yt_api: YoutubeAPI):
    # Get list of videos
    for video in yt_api.list_playlist_videos(subscription.playlist_id):
        results = Video.objects.filter(video_id=video.getVideoId(), subscription=subscription)
        if len(results) == 0:
            log.info('New video for subscription "', subscription, '": ', video.getVideoId(), video.getTitle())
            create_video(video, subscription)


def __fetch_thumbnails_obj(iterable, obj_type, id_attr):
    for obj in iterable:
        if obj.icon_default.startswith("http"):
            obj.icon_default = fetch_thumbnail(obj.icon_default, obj_type, getattr(obj, id_attr), 'default')
        if obj.icon_best.startswith("http"):
            obj.icon_best = fetch_thumbnail(obj.icon_best, obj_type, getattr(obj, id_attr), 'best')
        obj.save()


def __fetch_thumbnails():
    # Fetch thumbnails
    log.info("Fetching channel thumbnails... ")
    __fetch_thumbnails_obj(Channel.objects.filter(icon_default__istartswith='http'), 'channel', 'channel_id')
    __fetch_thumbnails_obj(Channel.objects.filter(icon_best__istartswith='http'), 'channel', 'channel_id')

    log.info("Fetching subscription thumbnails... ")
    __fetch_thumbnails_obj(Subscription.objects.filter(icon_default__istartswith='http'), 'sub', 'playlist_id')
    __fetch_thumbnails_obj(Subscription.objects.filter(icon_best__istartswith='http'), 'sub', 'playlist_id')

    log.info("Fetching video thumbnails... ")
    __fetch_thumbnails_obj(Video.objects.filter(icon_default__istartswith='http'), 'video', 'video_id')
    __fetch_thumbnails_obj(Video.objects.filter(icon_best__istartswith='http'), 'video', 'video_id')


def synchronize():
    log.info("Running scheduled synchronization... ")

    # Sync subscribed playlists/channels
    log.info("Sync - checking for new videos")
    yt_api = YoutubeAPI.build_public()
    for subscription in Subscription.objects.all():
        __synchronize_sub(subscription, yt_api)

    log.info("Sync - checking for videos to download")
    downloader_process_all()

    log.info("Sync - fetching missing thumbnails")
    __fetch_thumbnails()

    log.info("Synchronization finished.")


def schedule_synchronize():
    trigger = CronTrigger.from_crontab(settings.get('global', 'SynchronizationSchedule'))
    scheduler.instance.add_job(synchronize, trigger, max_instances=1)
