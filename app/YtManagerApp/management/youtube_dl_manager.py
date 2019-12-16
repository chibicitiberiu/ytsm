import logging
import os
import subprocess
import sys

import requests
from django.conf import settings as dj_settings

LATEST_URL = "https://yt-dl.org/downloads/latest/youtube-dl"
GITHUB_API_LATEST_RELEASE = "https://api.github.com/repos/ytdl-org/youtube-dl/releases/latest"
log = logging.getLogger("YoutubeDlManager")


class YoutubeDlException(Exception):
    pass


class YoutubeDlNotInstalledException(YoutubeDlException):
    pass


class YoutubeDlRuntimeException(YoutubeDlException):
    pass


class YoutubeDlManager(object):

    def __init__(self):
        self.verbose = False
        self.progress = False

    def _get_path(self):
        return os.path.join(dj_settings.DATA_DIR, 'youtube-dl')

    def _check_installed(self, path):
        return os.path.isfile(path) and os.access(path, os.X_OK)

    def _get_run_args(self):
        run_args = []
        if self.verbose:
            run_args.append('-v')
        if self.progress:
            run_args.append('--newline')
        else:
            run_args.append('--no-progress')

        return run_args

    def run(self, *args):
        path = self._get_path()
        if not self._check_installed(path):
            log.error("Cannot run youtube-dl, it is not installed!")
            raise YoutubeDlNotInstalledException

        run_args = self._get_run_args()
        ret = subprocess.run([sys.executable, path, *run_args, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout = ret.stdout.decode('utf-8')
        if len(stdout) > 0:
            log.info("YoutubeDL: " + stdout)

        stderr = ret.stderr.decode('utf-8')
        if len(stderr) > 0:
            log.error("YoutubeDL: " + stderr)

        if ret.returncode != 0:
            raise YoutubeDlRuntimeException()

        return stdout

    def get_installed_version(self):
        return self.run('--version')

    def get_latest_version(self):
        resp = requests.get(GITHUB_API_LATEST_RELEASE, allow_redirects=True)
        resp.raise_for_status()

        info = resp.json()
        return info['tag_name']

    def install(self):
        # Check if we are running the latest version
        latest = self.get_latest_version()
        try:
            current = self.get_installed_version()
        except YoutubeDlNotInstalledException:
            current = None
        if latest == current:
            log.info(f"Running latest youtube-dl version ({current})!")
            return

        # Download latest
        resp = requests.get(LATEST_URL, allow_redirects=True, stream=True)
        resp.raise_for_status()

        path = self._get_path()
        with open(path + ".tmp", "wb") as f:
            for chunk in resp.iter_content(10 * 1024):
                f.write(chunk)

        # Replace
        os.unlink(path)
        os.rename(path + ".tmp", path)
        os.chmod(path, 555)

        # Test run
        newver = self.get_installed_version()
        if current is None:
            log.info(f"Installed youtube-dl version {newver}.")
        else:
            log.info(f"Upgraded youtube-dl from version {current} to {newver}.")
