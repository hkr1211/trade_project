from django import template

register = template.Library()

@register.filter(name='replace_str')
def replace_str(value, arg):
    try:
        src, dst = arg.split('|', 1)
    except ValueError:
        return value
    return str(value).replace(src, dst)