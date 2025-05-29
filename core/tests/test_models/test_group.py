import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import Group, Customer


@pytest.mark.django_db
class TestGroupModel:
    def test_group_creation(self, user_factory):
        """Test basic group creation"""
        creator = user_factory()
        group = Group.objects.create(
            group_name="Test Group",
            created_by=creator,
            size=5,
            amount=Decimal('100.00'),
            cycle_duration=6
        )
        assert group.members.count() == 0
        assert str(group) == "Test Group (Created by: {}) Value : 100.00".format(creator.username)

    def test_rotate_recipient(self, group_factory, user_factory):
        """Test recipient rotation logic"""
        members = [user_factory() for _ in range(3)]
        group = group_factory(members=members, size=3)

        # First rotation
        group.rotate_recipient()
        assert group.current_recipient == members[0]

        # Second rotation
        group.rotate_recipient()
        assert group.current_recipient == members[1]

    def test_invalid_group_size(self, user_factory):
        """Test validation for group size"""
        creator = user_factory()
        group = Group(
            group_name="Invalid Group",
            created_by=creator,
            size=1,  # Too small
            amount=Decimal('100.00')
        )
        with pytest.raises(ValidationError) as excinfo:
            group.full_clean()
        assert "Group size must be at least 2" in str(excinfo.value)

    def test_completed_group_cant_reactivate(self, group_factory):
        """Test state transition validation"""
        group = group_factory(all_cycles_completed_state=True, is_active=False)
        group.is_active = True
        with pytest.raises(ValidationError) as excinfo:
            group.save()
        assert "Cannot reactivate a completed group" in str(excinfo.value)