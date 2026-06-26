from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_remark(record):
    """Get remarks from attendance record"""
    if record is None:
        return ''
    return getattr(record, 'remarks', '') or ''