from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, JsonResponse
from .models import SubscriptionFolder, Subscription

def get_children_recurse(parent_id):
    children = []

    for folder in SubscriptionFolder.objects.filter(parent_id=parent_id).order_by('name'):
        children.append({
            "id" : "folder" + str(folder.id),
            "text" : folder.name,
            "type" : "folder",
            "children" : get_children_recurse(folder.id)
        })

    for sub in Subscription.objects.filter(parent_folder_id=parent_id).order_by('name'):
        children.append({
            "id" : "sub" + str(sub.id),
            "type" : "sub",
            "text" : sub.name
        })

    return children


def get_folders(parent_id, path = ""):
    folders = []

    for folder in SubscriptionFolder.objects.filter(parent_id=parent_id).order_by('name'):
        folder_path = path + "/" + folder.name 
        folders.append({
            "id" : "folder" + str(folder.id),
            "text" : folder_path
        })
        folders.extend(get_folders(folder.id, folder_path))

    return folders


def ajax_get_children(request: HttpRequest):
    return JsonResponse(get_children_recurse(None), safe=False)

def ajax_get_folders(request: HttpRequest):
    return JsonResponse(get_folders(None), safe=False)

def index(request: HttpRequest):
    context = {}
    return render(request, 'YtManagerApp/index.html', context)