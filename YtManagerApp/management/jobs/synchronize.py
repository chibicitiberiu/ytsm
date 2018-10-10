from YtManagerApp.models import *
import logging


def synchronize():
    logger = logging.getLogger('sync')

    logger.info("Running scheduled synchronization... ")

    # Sync subscribed playlists/channels
    yt_api = YoutubeAPI.build_public()
    for subscription in Subscription.objects.all():
        SubscriptionManager.__synchronize(subscription, yt_api)

    # Fetch thumbnails
    logger.info("Fetching channel thumbnails... ")
    for ch in Channel.objects.filter(icon_default__istartswith='http'):
        ch.icon_default = SubscriptionManager.__fetch_thumbnail(ch.icon_default, 'channel', ch.channel_id, 'default')
        ch.save()

    for ch in Channel.objects.filter(icon_best__istartswith='http'):
        ch.icon_best = SubscriptionManager.__fetch_thumbnail(ch.icon_best, 'channel', ch.channel_id, 'best')
        ch.save()

    logger.info("Fetching subscription thumbnails... ")
    for sub in Subscription.objects.filter(icon_default__istartswith='http'):
        sub.icon_default = SubscriptionManager.__fetch_thumbnail(sub.icon_default, 'sub', sub.playlist_id, 'default')
        sub.save()

    for sub in Subscription.objects.filter(icon_best__istartswith='http'):
        sub.icon_best = SubscriptionManager.__fetch_thumbnail(sub.icon_best, 'sub', sub.playlist_id, 'best')
        sub.save()

    logger.info("Fetching video thumbnails... ")
    for vid in Video.objects.filter(icon_default__istartswith='http'):
        vid.icon_default = SubscriptionManager.__fetch_thumbnail(vid.icon_default, 'video', vid.video_id, 'default')
        vid.save()

    for vid in Video.objects.filter(icon_best__istartswith='http'):
        vid.icon_best = SubscriptionManager.__fetch_thumbnail(vid.icon_best, 'video', vid.video_id, 'best')
        vid.save()

    print("Downloading videos...")
    Downloader.download_all()

    print("Synchronization finished.")