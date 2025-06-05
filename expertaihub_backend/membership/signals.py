from datetime import date
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Membership, MonthlyUsage

User = get_user_model()

@receiver(post_save, sender=User)
def create_membership_and_usage(sender, instance, created, **kwargs):
    if not created:
        return

    # Create the Membership (defaults handle free + 15)
    Membership.objects.create(user=instance)

    # Seed this month’s usage row (count=0)
    first_of_month = date.today().replace(day=1)
    MonthlyUsage.objects.create(user=instance, period=first_of_month)
