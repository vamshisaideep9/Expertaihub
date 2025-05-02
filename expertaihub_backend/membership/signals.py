# membership/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Membership

User = get_user_model()

@receiver(post_save, sender=User)
def create_membership(sender, instance, created, **kwargs):
    if created:
        Membership.objects.create(
            user=instance,
            membership_type='free',
            is_active=True
        )
