from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.edit import FormMixin
from django.conf import settings
from django.core.paginator import Paginator
from YtManagerApp.management.videos import get_videos
from YtManagerApp.models import Subscription, SubscriptionFolder, VIDEO_ORDER_CHOICES, VIDEO_ORDER_MAPPING
from YtManagerApp.services import Services
from YtManagerApp.utils import youtube, subscription_file_parser
from YtManagerApp.views.controls.modal import ModalMixin

import logging


class VideoFilterForm(forms.Form):
    CHOICES_SHOW_WATCHED = (
        ('y', 'Watched'),
        ('n', 'Not watched'),
        ('all', '(All)')
    )

    CHOICES_SHOW_DOWNLOADED = (
        ('y', 'Downloaded'),
        ('n', 'Not downloaded'),
        ('all', '(All)')
    )

    MAPPING_SHOW = {
        'y': True,
        'n': False,
        'all': None
    }

    CHOICES_RESULT_COUNT = (
        (25, 25),
        (50, 50),
        (100, 100),
        (200, 200)
    )

    query = forms.CharField(label='', required=False)
    sort = forms.ChoiceField(label='Sort:', choices=VIDEO_ORDER_CHOICES, initial='newest')
    show_watched = forms.ChoiceField(label='Show only: ', choices=CHOICES_SHOW_WATCHED, initial='all')
    show_downloaded = forms.ChoiceField(label='', choices=CHOICES_SHOW_DOWNLOADED, initial='all')
    subscription_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
    folder_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
    page = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
    results_per_page = forms.ChoiceField(label='Results per page: ', choices=CHOICES_RESULT_COUNT, initial=50)

    def __init__(self, data=None):
        super().__init__(data, auto_id='form_video_filter_%s')
        self.helper = FormHelper()
        self.helper.form_id = 'form_video_filter'
        self.helper.form_class = 'form-inline'
        self.helper.form_method = 'POST'
        self.helper.form_action = 'ajax_get_videos'
        self.helper.field_class = 'mr-1'
        self.helper.label_class = 'ml-2 mr-1 no-asterisk'

        self.helper.layout = Layout(
            Field('query', placeholder='Search'),
            'sort',
            'show_watched',
            'show_downloaded',
            'subscription_id',
            'folder_id',
            'page',
            'results_per_page'
        )

    def clean_sort(self):
        data = self.cleaned_data['sort']
        return VIDEO_ORDER_MAPPING[data]

    def clean_show_downloaded(self):
        data = self.cleaned_data['show_downloaded']
        return VideoFilterForm.MAPPING_SHOW[data]

    def clean_show_watched(self):
        data = self.cleaned_data['show_watched']
        return VideoFilterForm.MAPPING_SHOW[data]


def __tree_folder_id(fd_id):
    if fd_id is None:
        return '#'
    return 'folder' + str(fd_id)


def __tree_sub_id(sub_id):
    if sub_id is None:
        return '#'
    return 'sub' + str(sub_id)


def index(request: HttpRequest):

    if not Services.appConfig.initialized:
        return redirect('first_time_0')

    context = {
        'config_errors': settings.CONFIG_ERRORS,
        'config_warnings': settings.CONFIG_WARNINGS,
    }
    if request.user.is_authenticated:
        context.update({
            'filter_form': VideoFilterForm(),
        })
        return render(request, 'YtManagerApp/index.html', context)
    else:
        return render(request, 'YtManagerApp/index_unauthenticated.html', context)


@login_required
def ajax_get_tree(request: HttpRequest):

    def visit(node):
        if isinstance(node, SubscriptionFolder):
            return {
                "id": __tree_folder_id(node.id),
                "text": node.name,
                "type": "folder",
                "state": {"opened": True},
                "parent": __tree_folder_id(node.parent_id)
            }
        elif isinstance(node, Subscription):
            return {
                "id": __tree_sub_id(node.id),
                "type": "sub",
                "text": node.name,
                "icon": node.thumbnail,
                "parent": __tree_folder_id(node.parent_folder_id)
            }

    result = SubscriptionFolder.traverse(None, request.user, visit)
    return JsonResponse(result, safe=False)


@login_required
def ajax_get_videos(request: HttpRequest):
    if request.method == 'POST':
        form = VideoFilterForm(request.POST)
        if form.is_valid():
            videos = get_videos(
                user=request.user,
                sort_order=form.cleaned_data['sort'],
                query=form.cleaned_data['query'],
                subscription_id=form.cleaned_data['subscription_id'],
                folder_id=form.cleaned_data['folder_id'],
                only_watched=form.cleaned_data['show_watched'],
                only_downloaded=form.cleaned_data['show_downloaded']
            )

            paginator = Paginator(videos, form.cleaned_data['results_per_page'])
            videos = paginator.get_page(form.cleaned_data['page'])

            context = {
                'videos': videos
            }

            return render(request, 'YtManagerApp/index_videos.html', context)

    return HttpResponseBadRequest()


class SubscriptionFolderForm(forms.ModelForm):
    class Meta:
        model = SubscriptionFolder
        fields = ['name', 'parent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean_name(self):
        name = self.cleaned_data['name']
        return name.strip()

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        parent = cleaned_data.get('parent')

        # Check name is unique in parent folder
        args_id = []
        if self.instance is not None:
            args_id.append(~Q(id=self.instance.id))

        if SubscriptionFolder.objects.filter(parent=parent, name__iexact=name, *args_id).count() > 0:
            raise forms.ValidationError(
                'A folder with the same name already exists in the given parent directory!', code='already_exists')

        # Check for cycles
        if self.instance is not None:
            self.__test_cycles(parent)

    def __test_cycles(self, new_parent):
        visited = [self.instance.id]
        current = new_parent
        while current is not None:
            if current.id in visited:
                raise forms.ValidationError('Selected parent would create a parenting cycle!', code='parenting_cycle')
            visited.append(current.id)
            current = current.parent


class CreateFolderModal(LoginRequiredMixin, ModalMixin, CreateView):
    template_name = 'YtManagerApp/controls/folder_create_modal.html'
    form_class = SubscriptionFolderForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class UpdateFolderModal(LoginRequiredMixin, ModalMixin, UpdateView):
    template_name = 'YtManagerApp/controls/folder_update_modal.html'
    model = SubscriptionFolder
    form_class = SubscriptionFolderForm


class DeleteFolderForm(forms.Form):
    keep_subscriptions = forms.BooleanField(required=False, initial=False, label="Keep subscriptions")


class DeleteFolderModal(LoginRequiredMixin, ModalMixin, FormMixin, DeleteView):
    template_name = 'YtManagerApp/controls/folder_delete_modal.html'
    model = SubscriptionFolder
    form_class = DeleteFolderForm

    def __init__(self, *args, **kwargs):
        self.object = None
        super().__init__(*args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object.delete_folder(keep_subscriptions=form.cleaned_data['keep_subscriptions'])
        return super().form_valid(form)


class CreateSubscriptionForm(forms.ModelForm):
    playlist_url = forms.URLField(label='Playlist/Channel URL')

    class Meta:
        model = Subscription
        fields = ['parent_folder', 'auto_download',
                  'download_limit', 'download_order', "automatically_delete_watched"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.yt_api = youtube.YoutubeAPI.build_public()
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'playlist_url',
            'parent_folder',
            HTML('<hr>'),
            HTML('<h5>Download configuration overloads</h5>'),
            'auto_download',
            'download_limit',
            'download_order',
            'automatically_delete_watched'
        )

    def clean_playlist_url(self):
        playlist_url: str = self.cleaned_data['playlist_url']
        try:
            parsed_url = self.yt_api.parse_url(playlist_url)
        except youtube.InvalidURL as e:
            raise forms.ValidationError(str(e))

        is_playlist = 'playlist' in parsed_url
        is_channel = parsed_url['type'] in ('channel', 'user', 'channel_custom')

        if not is_channel and not is_playlist:
            raise forms.ValidationError('The given URL must link to a channel or a playlist!')

        return playlist_url


class CreateSubscriptionModal(LoginRequiredMixin, ModalMixin, CreateView):
    template_name = 'YtManagerApp/controls/subscription_create_modal.html'
    form_class = CreateSubscriptionForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        api = youtube.YoutubeAPI.build_public()
        try:
            form.instance.fetch_from_url(form.cleaned_data['playlist_url'], api)
        except youtube.InvalidURL as e:
            return self.modal_response(form, False, str(e))
        except ValueError as e:
            return self.modal_response(form, False, str(e))
        # except youtube.YoutubeUserNotFoundException:
        #     return self.modal_response(
        #         form, False, 'Could not find an user based on the given URL. Please verify that the URL is correct.')
        # except youtube.YoutubePlaylistNotFoundException:
        #     return self.modal_response(
        #         form, False, 'Could not find a playlist based on the given URL. Please verify that the URL is correct.')
        # except youtube.YoutubeException as e:
        #     return self.modal_response(
        #         form, False, str(e))
        # except youtube.APIError as e:
        #     return self.modal_response(
        #         form, False, 'An error occurred while communicating with the YouTube API: ' + str(e))

        return super().form_valid(form)


class UpdateSubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['name', 'parent_folder', 'auto_download',
                  'download_limit', 'download_order', "automatically_delete_watched"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'name',
            'parent_folder',
            HTML('<hr>'),
            HTML('<h5>Download configuration overloads</h5>'),
            'auto_download',
            'download_limit',
            'download_order',
            'automatically_delete_watched'
        )


class UpdateSubscriptionModal(LoginRequiredMixin, ModalMixin, UpdateView):
    template_name = 'YtManagerApp/controls/subscription_update_modal.html'
    model = Subscription
    form_class = UpdateSubscriptionForm


class DeleteSubscriptionForm(forms.Form):
    keep_downloaded_videos = forms.BooleanField(required=False, initial=False, label="Keep downloaded videos")


class DeleteSubscriptionModal(LoginRequiredMixin, ModalMixin, FormMixin, DeleteView):
    template_name = 'YtManagerApp/controls/subscription_delete_modal.html'
    model = Subscription
    form_class = DeleteSubscriptionForm

    def __init__(self, *args, **kwargs):
        self.object = None
        super().__init__(*args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object.delete_subscription(keep_downloaded_videos=form.cleaned_data['keep_downloaded_videos'])
        return super().form_valid(form)


class ImportSubscriptionsForm(forms.Form):
    TRUE_FALSE_CHOICES = (
        (None, '(default)'),
        (True, 'Yes'),
        (False, 'No')
    )

    VIDEO_ORDER_CHOICES_WITH_EMPTY = (
        ('', '(default)'),
        *VIDEO_ORDER_CHOICES,
    )

    file = forms.FileField(label='File to import',
                           help_text='Supported file types: OPML, subscription list')
    parent_folder = forms.ModelChoiceField(SubscriptionFolder.objects, required=False)
    auto_download = forms.ChoiceField(choices=TRUE_FALSE_CHOICES, required=False)
    download_limit = forms.IntegerField(required=False)
    download_order = forms.ChoiceField(choices=VIDEO_ORDER_CHOICES_WITH_EMPTY, required=False)
    automatically_delete_watched = forms.ChoiceField(choices=TRUE_FALSE_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.yt_api = youtube.YoutubeAPI.build_public()
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'file',
            'parent_folder',
            HTML('<hr>'),
            HTML('<h5>Download configuration overloads</h5>'),
            'auto_download',
            'download_limit',
            'download_order',
            'automatically_delete_watched'
        )

    def __clean_empty_none(self, name: str):
        data = self.cleaned_data[name]
        if isinstance(data, str) and len(data) == 0:
            return None
        return data

    def __clean_boolean(self, name: str):
        data = self.cleaned_data[name]
        if isinstance(data, str) and len(data) == 0:
            return None
        if isinstance(data, str):
            return data == 'True'
        return data

    def clean_auto_download(self):
        return self.__clean_boolean('auto_download')

    def clean_automatically_delete_watched(self):
        return self.__clean_boolean('automatically_delete_watched')

    def clean_download_order(self):
        return self.__clean_empty_none('download_order')


class ImportSubscriptionsModal(LoginRequiredMixin, ModalMixin, FormView):
    template_name = 'YtManagerApp/controls/subscriptions_import_modal.html'
    form_class = ImportSubscriptionsForm

    def form_valid(self, form):
        file = form.cleaned_data['file']

        # Parse file
        try:
            url_list = list(subscription_file_parser.parse(file))
        except subscription_file_parser.FormatNotSupportedError:
            return super().modal_response(form, success=False,
                                          error_msg="The file could not be parsed! "
                                                    "Possible problems: format not supported, file is malformed.")

        print(form.cleaned_data)

        # Create subscriptions
        api = youtube.YoutubeAPI.build_public()
        for url in url_list:
            sub = Subscription()
            sub.user = self.request.user
            sub.parent_folder = form.cleaned_data['parent_folder']
            sub.auto_download = form.cleaned_data['auto_download']
            sub.download_limit = form.cleaned_data['download_limit']
            sub.download_order = form.cleaned_data['download_order']
            sub.automatically_delete_watched = form.cleaned_data["automatically_delete_watched"]
            try:
                sub.fetch_from_url(url, api)
            except Exception as e:
                logging.error("Import subscription error - error processing URL %s: %s", url, e)
                continue

            sub.save()

        return super().form_valid(form)
