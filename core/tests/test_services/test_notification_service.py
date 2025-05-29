import pytest
from unittest.mock import patch
from django.core import mail
from core.services import NotificationService
from core.models import Customer


@pytest.mark.django_db
class TestNotificationService:
    def test_send_email_notification(self, settings):
        """Test email sending functionality"""
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

        context = {'user': {'first_name': 'Test'}}
        result = NotificationService.send_email_notification(
            subject="Test Email",
            template_name="welcome_email",
            context=context,
            recipient_email="test@example.com"
        )

        assert result is True
        assert len(mail.outbox) == 1
        assert "Test Email" in mail.outbox[0].subject

    @patch('logging.error')
    def test_failed_email_notification(self, mock_logging, settings):
        """Test email failure handling"""
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

        # Force an error
        with patch('django.core.mail.send_mail', side_effect=Exception("SMTP error")):
            result = NotificationService.send_email_notification(
                subject="Test Email",
                template_name="welcome_email",
                context={},
                recipient_email="test@example.com"
            )

        assert result is False
        assert mock_logging.called

    def test_create_notification(self, user_factory):
        """Test notification creation"""
        user = user_factory()
        group = None  # Can use group_factory if needed

        NotificationService.create_notification(
            user=user,
            message="Test notification",
            notification_type="system",
            related_group=group
        )

        assert user.notifications.count() == 1
        notification = user.notifications.first()
        assert notification.message == "Test notification"