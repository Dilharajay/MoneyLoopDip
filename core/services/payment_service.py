from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from core.models import Contribution, Payout, Notification, Group, Transaction

import logging

from core.services import NotificationService

logger = logging.getLogger(__name__)

class DummyPaymentService:

    def __init__(self):
        pass

    @staticmethod
    def has_user_contributed_in_current_cycle(group, user):
        """Check if user has already contributed in the current cycle"""
        # Get the start of the current cycle (assuming monthly cycles)
        if group.next_payout_date:
            cycle_start = group.next_payout_date - timedelta(days=30)
        else:
            cycle_start = group.start_date

        return Contribution.objects.filter(
            group=group,
            user=user,
            date__gte=cycle_start,
            is_verified=True
        ).exists()

    @staticmethod
    def process_contribution(contribution, user_email):
        """Process contribution with duplicate payment prevention"""
        try:
            # Check if group is still active
            if contribution.group.all_cycles_completed_state:
                return {
                    'success': False,
                    'message': 'All contribution cycles for this group are already completed',
                }

            # Check if user has already contributed in this cycle
            if DummyPaymentService.has_user_contributed_in_current_cycle(contribution.group, contribution.user):
                return {
                    'success': False,
                    'message': 'You have already contributed in this cycle',
                }

            # Validate contribution amount
            if contribution.amount <= Decimal('0.00'):
                raise ValueError("Invalid contribution amount")

            # Check if amount matches group requirement
            if contribution.amount != contribution.group.amount:
                return {
                    'success': False,
                    'message': f'Contribution amount must be exactly {contribution.group.amount}',
                }

            # Process the payment (simulated)
            contribution.is_verified = True
            contribution.payment_reference = f"CONT_{contribution.id}_{int(timezone.now().timestamp())}"
            contribution.save()

            # Send confirmation email
            try:
                NotificationService.send_contribution_confirmation(contribution, user_email)
            except Exception as e:
                logger.error(f"Failed to send confirmation email to {user_email}: {e}")

            # Create transaction record
            Transaction.objects.create(
                group=contribution.group,
                transaction_id=contribution.payment_reference,
                amount=contribution.amount,
            )

            # Create notification
            Notification.objects.create(
                user=contribution.user,
                message=f"Contribution of ${contribution.amount} to "
                        f"{contribution.group.group_name} confirmed",
                notification_type='contribution_confirmed',
                related_group=contribution.group,
                related_payment=contribution
            )

            # Check if all members have contributed in this cycle
            all_members_contributed = all(
                DummyPaymentService.has_user_contributed_in_current_cycle(
                    contribution.group,
                    member
                )
                for member in contribution.group.members.all()
            )

            # If all members contributed, rotate recipient
            if all_members_contributed:
                contribution.group.is_active = False
                contribution.save()

            return {
                'success': True,
                'transaction_id': contribution.payment_reference,
                'message': 'Payment processed successfully'
            }

        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Payment processing failed'
            }
    '''
    @staticmethod
    def process_monthly_payouts():
        """Simulate monthly payouts with rotating recipients"""
        try:
            """Process all monthly payouts for active groups"""
            from core.models import Group
            today = timezone.now().date()

            # Get groups due for payout today
            groups = Group.objects.filter(
                next_payout_date__lte=today,
                is_active=True,
                all_cycles_completed_state=False,
                is_processing_payout=False
            )

            for group in groups:
                try:
                    # Lock the group to prevent concurrent processing
                    group.is_processing_payout = True
                    group.save()

                    # Process payout for current recipient
                    if group.current_recipient:
                        # Calculate amount with service charge (3% example)
                        service_charge = group.amount * Decimal('0.03')
                        payout_amount = group.amount - service_charge

                        # Create payout record
                        payout = Payout.objects.create(
                            group=group,
                            recipient=group.current_recipient,
                            amount=payout_amount,
                            payout_date=today,
                            is_completed=True,
                            transaction_reference=f"PYT-{group.id}-{today.strftime('%Y%m%d')}"
                        )

                        # Record service charge transaction
                        Transaction.objects.create(
                            group=group,
                            transaction_id=f"SVC-{group.id}-{today.strftime('%Y%m%d')}",
                            amount=service_charge,
                            is_service_charge=True
                        )

                        # Send notification to recipient
                        Notification.objects.create(
                            user=group.current_recipient,
                            message=f"You have received a payout of ${payout_amount} "
                                    f"from {group.group_name}",
                            notification_type='payout_received',
                            related_group=group
                        )

                        # Send email notification
                        try:
                            send_mail(
                                subject=f'Payout Received from {group.group_name}',
                                message=f'You have received ${payout_amount} from {group.group_name}.\n'
                                        f'Transaction Reference: {payout.transaction_reference}',
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[group.current_recipient.email],
                                fail_silently=False,
                            )
                        except Exception as e:
                            logger.error(f"Failed to send payout email: {e}")

                        # Rotate to next recipient
                        group.rotate_recipient()

                    # Update payout dates
                    group.last_payout_date = today
                    group.next_payout_date = today + timedelta(days=30)
                    group.is_processing_payout = False
                    group.save()

                except Exception as e:
                    logger.error(f"Failed to process payout for group {group.id}: {e}")
                    group.is_processing_payout = False
                    group.save()
                    return {
                        'success': False,
                        'error': f'Payout process failed for group {str(e)}',
                    }
            return {
                'success': True,
                'message': 'Payout processed successfully'
            }
        except Exception as e:
            logger.error(f"Failed to process monthly payouts: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to process monthly payouts'
            }
        '''