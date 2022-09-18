from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel

from django.views.debug import get_default_exception_reporter_filter
get_safe_settings = get_default_exception_reporter_filter().get_safe_settings

from .tracker import QueryTracker

_NAV_SUBTITLE_TPL = u'''
{% for o, n, t in operations %}
    {{ n }} {{ o }}{{ n|pluralize }} in {{ t }}ms<br/>

    {% if forloop.last and forloop.counter0 %}
        {{ count }} operation{{ count|pluralize }} in {{ time }}ms
    {% endif %}
{% endfor %}
'''


class MongoPanel(Panel):
    """Panel that shows information about MongoDB operations.
    """
    name = 'MongoDB'
    has_content = True
    template = 'mongo-panel.html'

    # def __init__(self, *args, **kwargs):
    #     super(MongoPanel, self).__init__(*args, **kwargs)
    #     operation_tracker.install_tracker()

    def title(self):
        return 'MongoDB Operations'

    def nav_title(self):
        return 'MongoDB'

    def nav_subtitle(self):
        stats = self.get_stats()
        count = len(stats['queries'])
        time_total = sum(list(map(lambda i: i['time'], stats['queries'])))
        return f'{count} queries in {round(time_total)} ms'

    def enable_instrumentation(self):
        QueryTracker.enable()

    def disable_instrumentation(self):
        QueryTracker.disable()

    def process_request(self, request):
        QueryTracker.reset()  # сбрасываем старые данные перед новым запросом
        result = super().process_request(request)
        QueryTracker._save_last_refresh_query() # сохраняем последний запрос find
        return result

    def generate_stats(self, request, response):
        # print('!! generate_stats')
        self.record_stats({
            'queries': QueryTracker.queries
        })

    # def process_request(self, request):
    #     operation_tracker.reset()

    # def process_response(self, request, response):
    #     self.record_stats({
    #         'queries': operation_tracker.queries,
    #         'inserts': operation_tracker.inserts,
    #         'updates': operation_tracker.updates,
    #         'removes': operation_tracker.removes
    #     })
    #
    # def generate_stats(self, request, response):
    #     self.record_stats({'a': 1})
