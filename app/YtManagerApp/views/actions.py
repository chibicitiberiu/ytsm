from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import View

from YtManagerApp.models import Video
from YtManagerApp.scheduler.jobs.synchronize_job import SynchronizeJob


class SyncNowView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        SynchronizeJob.schedule_now()
        return JsonResponse({
            'success': True
        })


class DeleteVideoFilesView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        video = Video.objects.get(id=kwargs['pk'])
        video.delete_files()
        return JsonResponse({
            'success': True
        })


class DownloadVideoFilesView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        video = Video.objects.get(id=kwargs['pk'])
        video.download()
        return JsonResponse({
            'success': True
        })


class MarkVideoWatchedView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        video = Video.objects.get(id=kwargs['pk'])
        video.mark_watched()
        return JsonResponse({
            'success': True
        })


class MarkVideoUnwatchedView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        video = Video.objects.get(id=kwargs['pk'])
        video.mark_unwatched()
        video.save()
        return JsonResponse({
            'success': True
        })
