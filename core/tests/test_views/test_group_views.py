import pytest
from django.urls import reverse
from core.models import Group, GroupInvitation


@pytest.mark.django_db
class TestGroupViews:
    def test_group_detail_view(self, client, group_factory, user_factory):
        """Test authorized access to group detail"""
        user = user_factory()
        group = group_factory(created_by=user)
        client.force_login(user)

        url = reverse('group_detail', kwargs={'group_id': group.id})
        response = client.get(url)

        assert response.status_code == 200
        assert group.group_name in str(response.content)

    def test_group_detail_unauthorized(self, client, group_factory, user_factory):
        """Test unauthorized access attempt"""
        owner = user_factory()
        stranger = user_factory()
        group = group_factory(created_by=owner)
        client.force_login(stranger)

        url = reverse('group_detail', kwargs={'group_id': group.id})
        response = client.get(url)

        assert response.status_code == 403

    def test_group_creation(self, client, user_factory):
        """Test group creation flow"""
        user = user_factory(role='A')  # Admin user
        client.force_login(user)

        url = reverse('add_group')
        response = client.post(url, {
            'group_name': 'New Test Group',
            'size': '5',
            'cycle_duration': '6',
            'amount': '100.00',
            'payment_method': 'bank',
            'members': []
        })

        assert response.status_code == 302  # Redirect after success
        assert Group.objects.filter(group_name='New Test Group').exists()

    def test_invitation_acceptance(self, client, group_factory, user_factory):
        """Test group invitation workflow"""
        inviter = user_factory()
        invitee = user_factory()
        group = group_factory(created_by=inviter)

        invitation = GroupInvitation.objects.create(
            group=group,
            email=invitee.email,
            invited_by=inviter
        )

        client.force_login(invitee)
        url = reverse('accept_invitation_web', kwargs={'invitation_id': invitation.id})
        response = client.get(url)

        assert response.status_code == 302
        assert invitee in group.members.all()
        invitation.refresh_from_db()
        assert invitation.status == 'accepted'