from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel

from django.views.debug import get_default_exception_reporter_filter
get_safe_settings = get_default_exception_reporter_filter().get_safe_settings

from debug_toolbar_mongo import operation_tracker
from . import tracker

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
        return 'nav_subtitle here'

    def enable_instrumentation(self):
        # operation_tracker.install_tracker()
        tracker.install()

    def process_request(self, request):
        tracker.reset()
        return super().process_request(request)

    def generate_stats(self, request, response):
        self.record_stats({
            'queries': tracker.queries
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
