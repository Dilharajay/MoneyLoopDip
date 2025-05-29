import pytest
from unittest.mock import patch
from core.tasks import process_monthly_payouts, send_daily_notifications


@pytest.mark.django_db
class TestCeleryTasks:
    @patch('core.services.payment_service.DummyPaymentService.process_monthly_payouts')
    def test_process_monthly_payouts(self, mock_process):
        """Test payout task execution"""
        mock_process.return_value = {'success': True}

        result = process_monthly_payouts.delay().get()
        assert result is True
        assert mock_process.called

    @patch('core.services.notification_service.NotificationService.send_payment_reminders')
    @patch('core.services.notification_service.NotificationService.send_late_payment_warnings')
    def test_send_daily_notifications(self, mock_late, mock_reminders):
        """Test notification task execution"""
        mock_reminders.return_value = True
        mock_late.return_value = True

        result = send_daily_notifications.delay().get()
        assert result is None  # No return value expected
        assert mock_reminders.called
        assert mock_late.called

    @patch('core.tasks.process_monthly_payouts.retry')
    @patch('core.services.payment_service.DummyPaymentService.process_monthly_payouts')
    def test_payout_task_retry(self, mock_process, mock_retry):
        """Test task retry on failure"""
        mock_process.side_effect = Exception("Test error")
        mock_retry.side_effect = Exception("Would retry")

        with pytest.raises(Exception):
            process_monthly_payouts.delay().get()

        assert mock_retry.called