from django.http import HttpResponseBadRequest, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, JsonResponse

from debug_toolbar.decorators import require_show_toolbar


@csrf_exempt
@require_show_toolbar
def mongo_explain(request):
    return JsonResponse({'result': 'Hello, world!'})