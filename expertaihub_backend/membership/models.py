from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Membership(models.Model):
    MEMBERSHIP_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="membership")
    membership_type = models.CharField(max_length=10, choices=MEMBERSHIP_CHOICES)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.membership_type.capitalize()}"
    



class MonthlyUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="monthly_usage")
    period = models.DateField(help_text="The first day of the month this record covers")
    count = models.PositiveBigIntegerField(default=0)

    class Meta:
        unique_together = ("user", "period")

    def increment(self):
        self.count = models.F("count")+1
        self.save(update_fields=["count"])
        self.refresh_from_db(fields=["count"]) 
