from django.db import models

class Badge(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True, null=True)  # path or icon name

    def __str__(self):
        return self.name