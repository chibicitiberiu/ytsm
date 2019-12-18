from YtManagerApp.models import Video
from YtManagerApp.services.scheduler.job import Job


class YouTubeDLUpdateJob(Job):
    name = "YouTubeDLUpdateJob"

    def __init__(self, job_execution):
        super().__init__(job_execution)

    def get_description(self):
        return f"Updating youtube-dl runtime"

    def run(self):
        from YtManagerApp.services import Services
        self.set_total_steps(1)
        Services.youtubeDLManager.install()
        self.progress_advance(1)
