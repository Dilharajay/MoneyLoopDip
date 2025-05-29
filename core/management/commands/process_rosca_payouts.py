from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Group
from core.services.group_service import GroupService

class Command(BaseCommand):
    help = 'Processes monthly cycles for ROSCA groups (contributions and payouts)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        running_groups = Group.objects.filter(is_active=True, all_cycles_completed_state=False)
        processed = 0
        for group in running_groups:
            # Only run for groups whose current cycle has ended (so you can trigger it immediately!)
            if not group.current_cycle_end or today >= group.current_cycle_end:
                recipient, payout = GroupService.process_monthly_payout(group)
                if recipient:
                    self.stdout.write(self.style.SUCCESS(f"Processed payout to {recipient.username} for {group.group_name}: {payout}"))
                    processed += 1
                else:
                    self.stdout.write(self.style.WARNING(f"Skipped group {group.group_name}; no eligible recipient or cycles completed"))
        if processed == 0:
            self.stdout.write(self.style.NOTICE("No groups required processing."))
