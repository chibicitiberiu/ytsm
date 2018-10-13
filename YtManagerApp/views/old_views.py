from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, JsonResponse
from YtManagerApp.models import SubscriptionFolder, Subscription
from YtManagerApp.management.management import FolderManager, SubscriptionManager


def get_children_recurse(parent_id):
    children = []

    for folder in SubscriptionFolder.objects.filter(parent_id=parent_id).order_by('name'):
        children.append({
            "id": "folder" + str(folder.id),
            "text": folder.name,
            "type": "folder",
            "state": {"opened": True},
            "children": get_children_recurse(folder.id)
        })

    for sub in Subscription.objects.filter(parent_folder_id=parent_id).order_by('name'):
        children.append({
            "id": "sub" + str(sub.id),
            "type": "sub",
            "text": sub.name,
            "icon": sub.icon_default
        })

    return children


def get_folders(parent_id, path=""):
    folders = []
    prefix = path + "/"
    if len(path) == 0:
        prefix = ""

    for folder in SubscriptionFolder.objects.filter(parent_id=parent_id).order_by('name'):
        folder_path = prefix + folder.name
        folders.append({
            "id": folder.id,
            "text": folder_path
        })
        folders.extend(get_folders(folder.id, folder_path))

    return folders


def ajax_get_children(request: HttpRequest):
    return JsonResponse(get_children_recurse(None), safe=False)


def ajax_get_folders(request: HttpRequest):
    return JsonResponse(get_folders(None), safe=False)


def ajax_edit_folder(request: HttpRequest):
    if request.method == 'POST':
        fid = request.POST['id']
        name = request.POST['name']
        parent_id = request.POST['parent']
        FolderManager.create_or_edit(fid, name, parent_id)

    return HttpResponse()


def ajax_delete_folder(request: HttpRequest, fid):
    FolderManager.delete(fid)
    return HttpResponse()


def ajax_edit_subscription(request: HttpRequest):
    if request.method == 'POST':
        sid = request.POST['id']
        name = request.POST['name']
        url = request.POST['url']
        parent_id = request.POST['parent']
        SubscriptionManager.create_or_edit(sid, url, name, parent_id)

    return HttpResponse()


def ajax_delete_subscription(request: HttpRequest, sid):
    SubscriptionManager.delete(sid)
    return HttpResponse()


def ajax_list_videos(request: HttpRequest):
    if request.method == 'POST':
        type = request.POST['type']
        id = request.POST['id']
        context = {}

        if type == 'sub':
            context['videos'] = SubscriptionManager.list_videos(int(id))
        else:
            context['videos'] = FolderManager.list_videos(int(id))

        return render(request, 'YtManagerApp/index_videos.html', context)


def index(request: HttpRequest):
    context = {}
    return render(request, 'YtManagerApp/index.html', context)

