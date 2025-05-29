import random
from django.utils import timezone
from core.models import Contribution, Group, Payout, Transaction
from core.services import NotificationService
from decimal import Decimal
from datetime import datetime

class GroupService:
    @staticmethod
    def select_random_recipient(group, cycle_number):
        # Exclude users who already received payout in this cycle
        eligible = group.members.exclude(
            id__in=Contribution.objects.filter(
                group=group, cycle_number=cycle_number
            ).values_list('user_id', flat=True)
        )
        if not eligible.exists():
            return None
        return random.choice(list(eligible))

    @staticmethod
    def process_monthly_payout(group):

        cycle_number = group.cycle_number
        # Get all contributions for this cycle, exclude recipient
        contributions = Contribution.objects.filter(group=group, cycle_number=cycle_number)
        if not contributions.exists():
            return None
        recipient = GroupService.select_random_recipient(group, cycle_number)
        if not recipient:
            group.all_cycles_completed_state = True
            group.is_active = False
            group.save()
            return None
        payout = sum(c.amount for c in contributions if c.user != recipient)

        # Service charge
        service_charge = payout * Decimal(0.05)

        total_payout = payout - service_charge

        # Create payout record

        payout = Payout.objects.create(
            group=group,
            recipient=recipient,
            amount=total_payout,
            payout_date=timezone.now().date(),
            is_completed=True,
            transaction_reference=f"PAYOUT-{int(timezone.now().timestamp())}"
        )

        # Send notification to recipient
        NotificationService.create_notification(
            user=recipient,
            message="Your monthly contribution payout has been done",
            notification_type='month_pay',
            related_group=group,
        )

        # Create transactions for monthly payout
        Transaction.objects.create(
            group=group,
            amount=total_payout,
            transaction_id = f"MONTH_PAY-{int(timezone.now().timestamp())}"
        )

        # Create transactions for service charge
        Transaction.objects.create(
            group=group,
            amount=service_charge,
            transaction_id=f"SERV_CH-{int(timezone.now().timestamp())}"
        )

        # Send Email
        NotificationService.send_monthly_payment_confirmation(payout, recipient.email)

        group.current_recipient = recipient
        group.cycle_number += 1
        if group.cycle_number > group.cycle_duration:
            group.all_cycles_completed_state = True
            group.is_active = False
        group.save()
        return recipient, total_payout
