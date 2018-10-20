from YtManagerApp import appconfig
from YtManagerApp.management.jobs.download_video import schedule_download_video
from YtManagerApp.models import Video, Subscription
from django.conf import settings
import logging
import requests
import mimetypes
import os
from urllib.parse import urljoin

log = logging.getLogger('downloader')


def __get_subscription_config(sub: Subscription):
    user_config = appconfig.get_user_config(sub.user)

    enabled = sub.auto_download
    if enabled is None:
        enabled = user_config.getboolean('user', 'AutoDownload')

    global_limit = -1
    if len(user_config.get('user', 'DownloadGlobalLimit')) > 0:
        global_limit = user_config.getint('user', 'DownloadGlobalLimit')

    limit = sub.download_limit
    if limit is None:
        limit = -1
        if len(user_config.get('user', 'DownloadSubscriptionLimit')) > 0:
            limit = user_config.getint('user', 'DownloadSubscriptionLimit')

    order = sub.download_order
    if order is None:
        order = user_config.get('user', 'DownloadOrder')

    return enabled, global_limit, limit, order


def downloader_process_subscription(sub: Subscription):
    log.info('Processing subscription %d [%s %s]', sub.id, sub.playlist_id, sub.id)

    enabled, global_limit, limit, order = __get_subscription_config(sub)
    log.info('Determined settings enabled=%s global_limit=%d limit=%d order="%s"', enabled, global_limit, limit, order)

    if enabled:
        videos_to_download = Video.objects\
            .filter(subscription=sub, downloaded_path__isnull=True, watched=False)\
            .order_by(order)

        log.info('%d download candidates.', len(videos_to_download))

        if global_limit > 0:
            global_downloaded = Video.objects.filter(subscription__user=sub.user, downloaded_path__isnull=False).count()
            allowed_count = max(global_limit - global_downloaded, 0)
            videos_to_download = videos_to_download[0:allowed_count]
            log.info('Global limit is set, can only download up to %d videos.', allowed_count)

        if limit > 0:
            sub_downloaded = Video.objects.filter(subscription=sub, downloaded_path__isnull=False).count()
            allowed_count = max(limit - sub_downloaded, 0)
            videos_to_download = videos_to_download[0:allowed_count]
            log.info('Limit is set, can only download up to %d videos.', allowed_count)

        # enqueue download
        for video in videos_to_download:
            log.info('Enqueuing video %d [%s %s] index=%d', video.id, video.video_id, video.name, video.playlist_index)
            schedule_download_video(video)

    log.info('Finished processing subscription %d [%s %s]', sub.id, sub.playlist_id, sub.id)


def downloader_process_all():
    for subscription in Subscription.objects.all():
        downloader_process_subscription(subscription)


def fetch_thumbnail(url, object_type, identifier, quality):

    log.info('Fetching thumbnail url=%s object_type=%s identifier=%s quality=%s', url, object_type, identifier, quality)

    # Make request to obtain mime type
    try:
        response = requests.get(url, stream=True)
    except requests.exceptions.RequestException as e:
        log.error('Failed to fetch thumbnail %s. Error: %s', url, e)
        return url

    ext = mimetypes.guess_extension(response.headers['Content-Type'])

    # Build file path
    file_name = f"{identifier}-{quality}{ext}"
    abs_path_dir = os.path.join(settings.MEDIA_ROOT, "thumbs", object_type)
    abs_path = os.path.join(abs_path_dir, file_name)

    # Store image
    try:
        os.makedirs(abs_path_dir, exist_ok=True)
        with open(abs_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        log.error('Error while downloading stream for thumbnail %s. Error: %s', url, e)
        return url
    except OSError as e:
        log.error('Error while writing to file %s for thumbnail %s. Error: %s', abs_path, url, e)
        return url

    # Return
    media_url = urljoin(settings.MEDIA_URL, f"thumbs/{object_type}/{file_name}")
    return media_url
