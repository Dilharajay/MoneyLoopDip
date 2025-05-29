from django.core.management.base import BaseCommand
from core.services.payment_service import DummyPaymentService

class Command(BaseCommand):
    help = 'Process monthly payouts for all eligible groups'

    def handle(self, *args, **options):
        self.stdout.write("Starting payout processing...")
        log = DummyPaymentService.process_monthly_payouts()
        if log['success']:
            self.stdout.write(self.style.SUCCESS("Payout processing completed"))
        else:
            self.stdout.write(self.style.ERROR(f"Payout processing failed"))