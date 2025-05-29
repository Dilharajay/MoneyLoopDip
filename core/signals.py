from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Contribution, Payout
from core.services.notification_service import NotificationService

@receiver(post_save, sender=Contribution)
def notify_contribution_confirmation(sender, instance, created, **kwargs):
    if instance.is_verified and not created:
        NotificationService.send_contribution_confirmation(instance)

@receiver(post_save, sender=Payout)
def notify_payout_received(sender, instance, created, **kwargs):
    if instance.is_completed and created:
        NotificationService.send_payout_notification(instance)