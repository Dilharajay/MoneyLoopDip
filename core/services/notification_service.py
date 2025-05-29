from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from core.models import Notification, Group, Contribution

import logging

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def send_email_notification(subject, template_name, context, recipient_email):
        """Send email notification"""
        try:
            text_message = render_to_string(f'emails/{template_name}.txt', context)
            html_message = render_to_string(f'emails/{template_name}.html', context)

            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logging.error(f'failed to send email to {recipient_email}: {str(e)}')
            return False

    @staticmethod
    def create_notification(user, message, notification_type, related_group=None, related_payment=None):
        """
        Create a notification record in the database.
        """
        Notification.objects.create(
            user=user,
            message=message,
            notification_type=notification_type,
            related_group=related_group,
            related_payment=related_payment,
        )

    @staticmethod
    def send_payment_reminders():
        from core.models import Group
        due_groups = Group.objects.filter(
            next_payout_date__lte=timezone.now() + timedelta(days=3),
            is_active=True
        ).prefetch_related('members')

        for group in due_groups:
            for member in group.members.all():
                if not DummyPaymentService.has_user_contributed_in_current_cycle(group, member):
                    NotificationService.send_email_notification(
                        subject=f"Payment Reminder for {group.group_name}",
                        template_name='payment_reminder',
                        recipient_email=member.email,
                        context={'group': group}
                    )

    @staticmethod
    def send_contribution_confirmation(contribution, user_email):
        """Send contribution confirmation"""
        context = {
            'amount': contribution.amount,
            'group_name': contribution.group.group_name,
            'payment_reference': contribution.payment_reference,
            'date': contribution.date,
        }

        # Send mail

        email_sent = NotificationService.send_email_notification(
            subject=f'Contribution Confirmed for {contribution.group.group_name}',
            template_name='contribution_confirmation',
            context=context,
            recipient_email=user_email,
        )

        return email_sent

    @staticmethod
    def send_monthly_payment_confirmation(payout, user_email):
        """Send monthly payment confirmation"""
        context = {
            'amount': payout.amount,
            'group_name': payout.group.group_name,
            'payment_reference': payout.transaction_reference,
            'payout_date': payout.payout_date,
            'recipient': payout.recipient,
        }

        # Send mail

        email_sent = NotificationService.send_email_notification(
            subject=f'Payout disbursement confirmed for {payout.recipient}',
            template_name='monthly_payout_confirmation',
            context=context,
            recipient_email=user_email,
        )

        return email_sent

    @staticmethod
    def send_welcome_email(user):
        """Send welcome email"""
        context = {
            'user': user,
        }

        # Send mail

        email_sent = NotificationService.send_email_notification(
            subject=f'Welcome to MoneyLoop {user.first_name}',
            template_name='welcome_email',
            context=context,
            recipient_email=user.email,
        )

        return email_sent
