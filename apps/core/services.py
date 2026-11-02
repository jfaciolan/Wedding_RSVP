"""Shared business logic."""

from django.db import transaction


@transaction.atomic
def move(obj, direction):
    """Swap an OrderedModel row with its neighbour. `direction` is "up" or "down"."""
    model = type(obj)
    items = list(model.objects.order_by("position", "pk"))
    # Normalise positions first so swaps are always well defined.
    for index, item in enumerate(items, start=1):
        if item.position != index:
            model.objects.filter(pk=item.pk).update(position=index)
            item.position = index
    index = next(i for i, item in enumerate(items) if item.pk == obj.pk)
    target = index - 1 if direction == "up" else index + 1
    if not 0 <= target < len(items):
        return
    a, b = items[index], items[target]
    model.objects.filter(pk=a.pk).update(position=b.position)
    model.objects.filter(pk=b.pk).update(position=a.position)
