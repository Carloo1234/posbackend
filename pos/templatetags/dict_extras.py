from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    """
    Template filter to safely get a key from a dict.
    Usage: {{ mydict|dict_get:"keyname" }}
    """
    if isinstance(d, dict):
        return d.get(key, False)
    return False