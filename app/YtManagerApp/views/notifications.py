from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse

from YtManagerApp.management.notification_manager import get_notifications


@login_required
def ajax_get_notifications(request: HttpRequest, last_id: int):
    user = request.user
    notifications = get_notifications(user, last_id)
    notifications = list(notifications)
    return JsonResponse(notifications, safe=False)
