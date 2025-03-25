from django import template
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

import pprint
import os
import bson.json_util

register = template.Library()

@register.filter(is_safe=True)
def json_script_bson(value, element_id=None):
    """
    Output value JSON-encoded, wrapped in a <script type="application/json">
    tag (with an optional id).
    """
    _json_script_escapes = {
        ord(">"): "\\u003E",
        ord("<"): "\\u003C",
        ord("&"): "\\u0026",
    }

    json_str = bson.json_util.dumps(value).translate(
        _json_script_escapes
    )
    if element_id:
        template = '<script id="{}" type="application/json">{}</script>'
        args = (element_id, mark_safe(json_str))
    else:
        template = '<script type="application/json">{}</script>'
        args = (mark_safe(json_str),)
    return format_html(template, *args)

@register.filter
def format_stack_trace(value):
    stack_trace = []
    fmt = (
        '<span class="path">{0}/</span>'
        '<span class="file">{1}</span> in <span class="func">{3}</span>'
        '(<span class="lineno">{2}</span>) <span class="code">{4}</span>'
    )
    for frame in value:
        params = map(escape, frame[0].rsplit('/', 1) + list(frame[1:]))
        stack_trace.append(fmt.format(*params))
    return mark_safe('\n'.join(stack_trace))

@register.filter
def embolden_file(path):
    head, tail = os.path.split(escape(path))
    return mark_safe(os.sep.join([head, '<strong>{0}</strong>'.format(tail)]))

@register.filter
def format_dict(value, width=60):
    return pprint.pformat(value, width=int(width))

@register.filter
def highlight(value, language):
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name
        from pygments.formatters import HtmlFormatter
    except ImportError:
        return value
    # Can't use class-based colouring because the debug toolbar's css rules
    # are more specific so take precedence
    formatter = HtmlFormatter(style='friendly', nowrap=True, noclasses=True)
    return highlight(value, get_lexer_by_name(language), formatter)
