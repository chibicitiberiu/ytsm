"""YtManager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.urls import path

from .views.auth import ExtendedLoginView, RegisterView, RegisterDoneView
from .views.index import index, ajax_get_tree, ajax_get_videos, CreateFolderModal, UpdateFolderModal, DeleteFolderModal
from .views import old_views

urlpatterns = [
    # Authentication URLs
    path('login/', ExtendedLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('register_done/', RegisterDoneView.as_view(), name='register_done'),
    path('', include('django.contrib.auth.urls')),

    # Ajax
    path('ajax/index_get_tree/', ajax_get_tree, name='ajax_index_get_tree'),
    path('ajax/index_get_videos/', ajax_get_videos, name='ajax_index_get_videos'),

    # Modals
    path('modal/create_folder/', CreateFolderModal.as_view(), name='modal_create_folder'),
    path('modal/create_folder/<int:parent_id>/', CreateFolderModal.as_view(), name='modal_create_folder'),
    path('modal/update_folder/<int:pk>/', UpdateFolderModal.as_view(), name='modal_update_folder'),
    path('modal/delete_folder/<int:pk>/', DeleteFolderModal.as_view(), name='modal_delete_folder'),

    # Index
    path('', index, name='home'),


    # Old stuff
    path('ajax/get_children', old_views.ajax_get_children, name='ajax_get_children'),
    path('ajax/get_folders', old_views.ajax_get_folders, name='ajax_get_folders'),
    path('ajax/edit_folder', old_views.ajax_edit_folder, name='ajax_edit_folder'),
    path('ajax/delete_folder/<int:fid>/', old_views.ajax_delete_folder, name='ajax_delete_folder'),
    path('ajax/edit_subscription', old_views.ajax_edit_subscription, name='ajax_edit_subscription'),
    path('ajax/delete_subscription/<int:sid>/', old_views.ajax_delete_subscription, name='ajax_delete_subscription'),
    path('ajax/list_videos', old_views.ajax_list_videos, name='ajax_list_videos'),
    # path('', old_views.index, name='home')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
