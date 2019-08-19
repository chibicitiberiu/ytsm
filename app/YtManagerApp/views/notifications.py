from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, JsonResponse

from YtManagerApp.models import JobExecution, JobMessage, JOB_STATES_MAP


@login_required
def ajax_get_running_jobs(request: HttpRequest):
    jobs = JobExecution.objects\
        .filter(status=JOB_STATES_MAP['running'])\
        .filter(Q(user__isnull=True) | Q(user=request.user))\
        .order_by('start_date')

    response = []

    for job in jobs:
        last_progress_message = JobMessage.objects\
            .filter(job=job, progress__isnull=False, suppress_notification=False)\
            .order_by('-timestamp').first()

        last_message = JobMessage.objects\
            .filter(job=job, suppress_notification=False)\
            .order_by('-timestamp').first()

        message = ''
        progress = 0

        if last_message is not None:
            message = last_message.message
        if last_progress_message is not None:
            progress = last_progress_message.progress

        response.append({
            'id': job.id,
            'description': job.description,
            'progress': progress,
            'message': message
        })

    return JsonResponse(response, safe=False)

