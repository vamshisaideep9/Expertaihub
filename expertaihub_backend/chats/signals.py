from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChatMessage

@receiver(post_save, sender=ChatMessage)
def touch_session_on_message(sender, instance: ChatMessage, created: bool, **kwargs):
    if created:
        instance.session.save(update_fields=["updated"])