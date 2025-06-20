# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def populate_username(sender, instance: CustomUser, created: bool, **kwargs):
    """
    Give each freshly-created user a unique, URL-safe `username`.
    Logic:
      1. derive a base from full_name -> email prefix -> 'user'
      2. slugify & truncate
      3. loop until unique, appending a 4-char suffix if needed
    """
    if not created or instance.username:
        return                                  # nothing to do

    base = (
        instance.full_name.split()[0]           # first word of name
        if instance.full_name
        else instance.email.split("@")[0]       # before the @
        if instance.email
        else "user"
    )
    base = slugify(base)[:20] or "user"

    username = base
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base}-{get_random_string(4).lower()}"

    # avoid infinite recursion: update only this field
    instance.username = username
    instance.save(update_fields=["username"])
