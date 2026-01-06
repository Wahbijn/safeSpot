from django.db import models
from django.conf import settings

class PredictionHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departure = models.CharField(max_length=100, blank=True, null=True)
    destination = models.CharField(max_length=100, blank=True, null=True)
    travel_time = models.DateTimeField(blank=True, null=True)
    weather = models.CharField(max_length=100, blank=True, null=True)
    risk_score = models.FloatField(default=0)  # 0–100
    is_safe = models.BooleanField(default=True)

    # Accident Cost Prediction Fields
    vehicle_make = models.CharField(max_length=100, blank=True, null=True)
    vehicle_model = models.CharField(max_length=100, blank=True, null=True)
    vehicle_year = models.IntegerField(blank=True, null=True)
    damage_type = models.CharField(max_length=50, blank=True, null=True)
    severity = models.IntegerField(blank=True, null=True)
    road_type = models.CharField(max_length=50, blank=True, null=True)

    # Cost Breakdown
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    repair_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medical_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vehicle_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Prediction Histories'

    def __str__(self):
        if self.departure and self.destination:
            return f"{self.user.username} - {self.departure} → {self.destination}"
        elif self.vehicle_make:
            return f"{self.user.username} - {self.vehicle_make} {self.vehicle_model} (${self.total_cost})"
        return f"{self.user.username} - Prediction {self.id}"
