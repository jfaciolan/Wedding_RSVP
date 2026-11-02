"""Shared abstract base models."""

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    """A model with exactly one row (pk=1), loaded with `Model.load()`."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Singleton rows cannot be deleted.")

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class OrderedModel(models.Model):
    """A model the Site Admin can reorder. Lower positions come first."""

    position = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ["position", "pk"]

    def save(self, *args, **kwargs):
        if self._state.adding and not self.position:
            last = type(self).objects.aggregate(models.Max("position"))["position__max"]
            self.position = (last or 0) + 1
        super().save(*args, **kwargs)
