# your_app/templatetags/attendance_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key).status
    except:
        return ''