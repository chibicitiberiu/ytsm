import logging
import os

from YtManagerApp import scheduler
from YtManagerApp.models import Video

log = logging.getLogger('video_downloader')


def delete_video(video: Video):
    log.info('Deleting video %d [%s %s]', video.id, video.video_id, video.name)
    count = 0

    try:
        for file in video.get_files():
            log.info("Deleting file %s", file)
            count += 1
            try:
                os.unlink(file)
            except OSError as e:
                log.error("Failed to delete file %s: Error: %s", file, e)

    except OSError as e:
        log.error("Failed to delete video %d [%s %s]. Error: %s", video.id, video.video_id, video.name, e)

    video.downloaded_path = None
    video.save()

    log.info('Deleted video %d successfully! (%d files) [%s %s]', video.id, count, video.video_id, video.name)


def schedule_delete_video(video: Video):
    """
    Schedules a download video job to run immediately.
    :param video:
    :return:
    """
    job = scheduler.scheduler.add_job(delete_video, args=[video])
    log.info('Scheduled delete video job video=(%s), job=%s', video, job.id)
