from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context, url_name):
    request = context['request']
    return 'is-active' if request.resolver_match.url_name == url_name else ''
