from django import template

register = template.Library()

@register.filter
def has_permission(manager, perm_name):
    if not manager:
        return False
    return manager.has_permission(perm_name)