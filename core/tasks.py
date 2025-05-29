from celery import shared_task
import pydevd
import logging

from core.models import Group
from core.services.group_service import GroupService
from core.services.payment_service import DummyPaymentService
from core.services.notification_service import NotificationService
from datetime import datetime, timezone

# Set up logging
logger = logging.getLogger(__name__)


# Debugging for remote debugging (change 'localhost' and port if needed)
def set_debugger():
    # Use your IDE's IP and port for remote debugging if required
    try:
        pydevd.settrace('localhost', port=5678, stdout_to_stderr=True, suspend=True)
        logger.debug("Debugger attached.")
    except Exception as e:
        logger.error(f"Failed to attach debugger: {e}")


# tasks.py
@shared_task()
def process_monthly_payouts():
    logger.info("Processing monthly payouts")
    try:
        from core.services.payment_service import DummyPaymentService
        DummyPaymentService.process_monthly_payouts()  # Let service handle date logic
    except Exception as e:
        logger.error(f"Payout processing failed: {str(e)}")
        self.retry(exc=e, countdown=60*5)  # Retry after 5 minutes

@shared_task
def send_daily_notifications():
    logger.info("Started send_daily_notifications task")

    # Debugger: Pause execution here to inspect values
    set_debugger()

    try:
        NotificationService.send_payment_reminders()
        NotificationService.send_late_payment_warnings()
        logger.info("Daily notifications sent.")
    except Exception as e:
        logger.error(f"Error sending notifications: {e}")


@shared_task
def process_disbursements():
    logger.info("Started process_disbursements task")

    # Debugger: Pause execution here to inspect values
    set_debugger()

    try:
        active_groups = Group.objects.filter(is_active=True)
        logger.info(f"Found {active_groups.count()} active groups.")

        for group in active_groups:
            logger.info(f"Processing disbursement for group: {group.name}")
            if group.next_payout_date == timezone.now().date():
                logger.info(f"Processing disbursement for group {group.name} as next payout date matches today.")
                GroupService.process_monthly_payout(group)
            else:
                logger.info(f"Group {group.name} does not have a payout today.")
    except Exception as e:
        logger.error(f"Error processing disbursements: {e}")

@shared_task(bind=True)
def dummy_task(self):
    print("Dummy task executed")
    return "Task executed"