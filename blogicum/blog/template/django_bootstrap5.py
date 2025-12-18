from django import template
from django.utils.safestring import mark_safe
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def bootstrap_css():
    return mark_safe(f'<link rel="stylesheet" href="{static("css/bootstrap.min.css")}">')


@register.simple_tag
def bootstrap_form(form):
    try:
        return mark_safe(form.as_p())
    except Exception:
        return ""


@register.simple_tag
def bootstrap_button(button_type="submit", content="Отправить"):
    return mark_safe(f'<button type="{button_type}" class="btn btn-primary">{content}</button>')
