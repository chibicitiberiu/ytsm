from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django import forms
from django.views.generic import CreateView, UpdateView, DeleteView, View
from django.views.generic.edit import FormMixin
from YtManagerApp.management.videos import get_videos
from YtManagerApp.models import Subscription, SubscriptionFolder, Video
from YtManagerApp.views.controls.modal import ModalMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div, HTML
from django.db.models import Q
from YtManagerApp.utils import youtube
from YtManagerApp.management.jobs.synchronize import schedule_synchronize_now


class SyncNowView(View):
    def post(self, *args, **kwargs):
        schedule_synchronize_now()
        return JsonResponse({
            'success': True
        })


class DeleteVideoFilesView(View):
    def post(self, *args, **kwargs):
        video = Video.objects.get(id=kwargs['pk'])
        video.delete_files()
        return JsonResponse({
            'success': True
        })


class DownloadVideoFilesView(View):
    def post(self, *args, **kwargs):
        video = Video.objects.get(id=kwargs['pk'])
        video.download()
        return JsonResponse({
            'success': True
        })


class MarkVideoWatchedView(View):
    def post(self, *args, **kwargs):
        video = Video.objects.get(id=kwargs['pk'])
        video.mark_watched()
        return JsonResponse({
            'success': True
        })


class MarkVideoUnwatchedView(View):
    def post(self, *args, **kwargs):
        video = Video.objects.get(id=kwargs['pk'])
        video.mark_unwatched()
        video.save()
        return JsonResponse({
            'success': True
        })
