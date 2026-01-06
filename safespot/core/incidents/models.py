from django.db import models
from django.conf import settings
from django.utils import timezone


# -----------------------------
# Shared choices
# -----------------------------
GUILTY_CHOICES = [
    ('me', 'Me'),
    ('other', 'Other Party'),
    ('both', 'Both'),
]


# -----------------------------
# Abstract base model
# -----------------------------
class BaseAccident(models.Model):
    description = models.TextField(blank=True, null=True)
    # Reporter info
    reporter_name = models.CharField(max_length=100)
    reporter_phone = models.CharField(max_length=20)
    reporter_cin = models.CharField(max_length=20)

    # Accident details
    accident_datetime = models.DateTimeField(default=timezone.now)
    localisation = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    car_type = models.CharField(max_length=50)
    reason = models.TextField()

    # Other party info
    other_name = models.CharField(max_length=100)
    other_cin = models.CharField(max_length=20)
    other_phone = models.CharField(max_length=20)

    # Responsibility
    guilty = models.CharField(
        max_length=10,
        choices=GUILTY_CHOICES
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_created"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


# -----------------------------
# Witness / Passenger Report
# -----------------------------
class UserAccidentReport(BaseAccident):
    """
    Simple accident report created by a passenger / witness.
    """

    def __str__(self):
        return f"Witness report by {self.reporter_name} - {self.accident_datetime:%Y-%m-%d %H:%M}"


# -----------------------------
# Main Accident Model
# -----------------------------
class Accident(BaseAccident):
    """
    Main accident entity visible to admin.
    Can be confirmed or canceled by users.
    """

    confirmations = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="confirmed_accidents",
        blank=True
    )

    cancellations = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="canceled_accidents",
        blank=True
    )

    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.localisation} - {self.accident_datetime:%Y-%m-%d %H:%M}"
