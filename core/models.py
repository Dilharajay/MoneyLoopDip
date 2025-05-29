import re
from datetime import timedelta, datetime, date

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.crypto import get_random_string
from decimal import Decimal
# Create your models here.

from django.contrib.auth.models import AbstractUser


def validate_nic(value):
    if not re.match(r'^(\d{9}[VXvx]|\d{12})$', value):
        raise ValidationError('Enter a valid Sri Lankan NIC number.')


class Customer(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    street_address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    zip_code = models.PositiveIntegerField(blank=True, null=True)
    nic = models.CharField(max_length=12, unique=True, validators=[validate_nic])
    ROLE_CHOICES = [
        ('A', 'Admin'),
        ('U', 'User'),
    ]
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, default='U')

    COUNTRY_CHOICES = [
        ('US', 'United States'),
        ('GB', 'United Kingdom'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
        ('IN', 'India'),
        ('LK', 'Sri Lanka'),
        ('DE', 'Germany'),
        ('FR', 'France'),
        ('JP', 'Japan'),
        ('CN', 'China'),
        ('BR', 'Brazil'),
        ('ZA', 'South Africa'),
        ('RU', 'Russia'),
    ]
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='LK')

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='customer_groups',
        related_query_name='customer',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='customer_user_permissions',
        related_query_name='customer',
    )


class Group(models.Model):
    group_name = models.CharField(max_length=100)
    created_by = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="admin_groups")
    members = models.ManyToManyField(Customer, related_name="joined_groups")
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(decimal_places=2, max_digits=10, default=0.00)

    # new fields
    current_recipient = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_recipient_groups'
    )
    next_payout_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    cycle_number = models.PositiveIntegerField(default=0)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('bank', 'Bank Transfer'),
            ('cash', 'Cash'),
        ],
        default='bank'
    )

    remaining_amount = models.DecimalField(decimal_places=2, max_digits=10, default=0.0)

    cycle_duration = models.PositiveIntegerField(default=1)
    start_date = models.DateField(default=date.today)
    all_cycles_completed_state = models.BooleanField(default=False)

    current_cycle_start = models.DateField(null=True, blank=True)
    current_cycle_end = models.DateField(null=True, blank=True)

    def rotate_recipient(self):
        members = list(self.members.order_by('id'))
        if not members or self.all_cycles_completed_state:
            return
        if not self.remaining_amount:
            self.remaining_amount = self.amount * Decimal(len(self.members.all()))
            self.save()
        if not self.all_cycles_completed_state:
            if not self.current_recipient:
                self.current_recipient = members[0]
                self.save()
            else:
                current_index = members.index(self.current_recipient)
                next_index = (current_index + 1)
                next_recipient = members[next_index]

                self.current_recipient = next_recipient
                self.next_payout_date = (self.next_payout_date or self.start_date) + timedelta(days=30)
                if self.cycle_number <= self.cycle_duration:
                    self.cycle_number += 1
                else:
                    self.all_cycles_completed_state = True
                    self.is_active = False
                self.save()

    def save(self, *args, **kwargs):
        # Set cycle dates when group is created
        if not self.pk:
            self.current_cycle_start = self.start_date
            self.current_cycle_end = self.start_date + timedelta(days=30)
        super().save(*args, **kwargs)

    def __str__(self):
        if not self.all_cycles_completed_state:
            return f"{self.group_name} (Created by: {self.created_by.username}) Value : {self.amount}"
        else:
            return f"{self.group_name} Has been completed making payments!"

class Contribution(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="contributions")
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)

    # new fields

    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_manual = models.BooleanField(default=True)  # Track if contribution was manual
    cycle_number = models.PositiveIntegerField(default=1)  # Track which cycle this belongs to

    class Meta:
        unique_together = ('group', 'user', 'date')

    def __str__(self):
        return f"{self.user.username} contributed ${self.amount} to {self.group.group_name}"


class Transaction(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="transactions")
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction #{self.transaction_id} - ${self.amount}"


class Payout(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='payouts')
    recipient = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payout_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    transaction_reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Payout to {self.recipient.username} - ${self.amount}"


# Adding notifications system

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('payment_due', 'Payment Due Reminder'),
        ('payout_received', 'Payout Received'),
        ('contribution_confirmed', 'Contribution Confirmed'),
        ('group_alert', 'Group Announcement'),
        ('system', 'System Notification'),
        ('month_pay', 'Monthly Payment'),
    ]

    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    notification_type = models.CharField(max_length=22, choices=NOTIFICATION_TYPES, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    related_payment = models.ForeignKey(Contribution, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.username}"


class GroupInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    token = models.CharField(max_length=50, unique=True)
    invited_by = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(32)
        super().save(*args, **kwargs)
