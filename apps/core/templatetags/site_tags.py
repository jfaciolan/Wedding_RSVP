from django import template

register = template.Library()


@register.simple_tag
def input_widget(field, hint=""):
    """Render a form field's widget with the site's input class and ARIA wiring."""
    attrs = {"class": "input"}
    described_by = []
    if hint:
        described_by.append(f"{field.auto_id}_hint")
    if field.errors:
        described_by.append(f"{field.auto_id}_error")
        attrs["aria-invalid"] = "true"
    if described_by:
        attrs["aria-describedby"] = " ".join(described_by)
    if field.field.required:
        attrs["aria-required"] = "true"
    return field.as_widget(attrs=attrs)


@register.filter
def get_item(mapping, key):
    return mapping.get(key)
