import pytest
from decimal import Decimal
from unittest.mock import patch
from core.services import DummyPaymentService
from core.models import Contribution, Group, Customer


@pytest.mark.django_db
class TestPaymentService:
    def test_successful_contribution(self, group_factory, user_factory):
        """Test normal contribution processing"""
        group = group_factory(amount=Decimal('100.00'), is_active=True)
        user = user_factory()
        group.members.add(user)

        contribution = Contribution.objects.create(
            group=group,
            user=user,
            amount=group.amount
        )

        with patch('core.services.notification_service.NotificationService.send_email_notification') as mock_send:
            result = DummyPaymentService.process_contribution(contribution, user.email)

        assert result['success'] is True
        contribution.refresh_from_db()
        assert contribution.is_verified is True
        assert mock_send.called

    def test_duplicate_contribution(self, group_factory, user_factory):
        """Test duplicate contribution prevention"""
        group = group_factory(amount=Decimal('100.00'))
        user = user_factory()
        group.members.add(user)

        # First contribution
        Contribution.objects.create(
            group=group,
            user=user,
            amount=group.amount,
            is_verified=True
        )

        # Second attempt
        new_contribution = Contribution.objects.create(
            group=group,
            user=user,
            amount=group.amount
        )

        result = DummyPaymentService.process_contribution(new_contribution, user.email)
        assert result['success'] is False
        assert "already contributed" in result['message']

    def test_invalid_amount(self, group_factory, user_factory):
        """Test amount validation"""
        group = group_factory(amount=Decimal('100.00'))
        user = user_factory()
        group.members.add(user)

        contribution = Contribution.objects.create(
            group=group,
            user=user,
            amount=Decimal('50.00')  # Wrong amount
        )

        result = DummyPaymentService.process_contribution(contribution, user.email)
        assert result['success'] is False
        assert "exactly 100.00" in result['message']