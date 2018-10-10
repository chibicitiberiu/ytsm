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
from django.urls import path
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from YtManagerApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ajax/get_children', views.ajax_get_children, name='ajax_get_children'),
    path('ajax/get_folders', views.ajax_get_folders, name='ajax_get_folders'),
    path('ajax/edit_folder', views.ajax_edit_folder, name='ajax_edit_folder'),
    path('ajax/delete_folder/<int:fid>/', views.ajax_delete_folder, name='ajax_delete_folder'),
    path('ajax/edit_subscription', views.ajax_edit_subscription, name='ajax_edit_subscription'),
    path('ajax/delete_subscription/<int:sid>/', views.ajax_delete_subscription, name='ajax_delete_subscription'),
    path('ajax/list_videos', views.ajax_list_videos, name='ajax_list_videos'),
    path(r'', views.index, name='home')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
