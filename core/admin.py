from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .models import  Customer, Group, Contribution, Transaction, Notification, Payout

from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect

from django.contrib.admin import AdminSite

"""# Register your custom user model with a custom admin class
class CustomerAdmin(UserAdmin):
    list_display = ('username', 'email', 'nic', 'role', 'is_staff')
    search_fields = ('username', 'email', 'nic')
    ordering = ('username',)

    # Add all fields you want to be editable in admin
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'nic', 'date_of_birth', 'phone')}),
        ('Address', {'fields': ('street_address', 'city', 'state', 'zip_code', 'country')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Group)
admin.site.register(Contribution)
admin.site.register(Transaction)
"""


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'country', 'role')
    list_filter = ('role', 'country', 'date_joined')
    search_fields = ('username', 'email', 'nic')
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = [
        ('Authentication', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'nic')}),
        ('Address', {'fields': ('street_address', 'city', 'state', 'zip_code', 'country')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
    ]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'created_by', 'size', 'amount', 'is_active', 'next_payout_date')
    list_filter = ('is_active', 'payment_method')
    search_fields = ('group_name', 'created_by__username')
    filter_horizontal = ('members',)
    fieldsets = [
        ('Basic Info', {'fields': ('group_name', 'created_by', 'members', 'size', 'amount')}),
        ('ROSCA Settings', {'fields': ('current_recipient', 'next_payout_date', 'cycle_number', 'is_active')}),
    ]

    @admin.action(description='Activate selected groups')
    def make_active(modeladmin, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate selected groups')
    def make_inactive(modeladmin, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='Process payouts for selected groups')
    def process_payouts(modeladmin, request, queryset):
        from payments.services import ROSCAService
        for group in queryset:
            ROSCAService.process_monthly_payouts(group)
        modeladmin.message_user(request, f"Processed payouts for {queryset.count()} groups")

    @admin.action(description="Process monthly payouts for selected groups")
    def process_monthly_payouts(modeladmin, request, queryset):
        for group in queryset:
            GroupService.process_monthly_payouts(group)

    actions = [make_active, make_inactive, process_payouts, process_monthly_payouts]


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'amount', 'date', 'is_verified')
    list_filter = ('is_verified', 'date')
    raw_id_fields = ('user', 'group')

    @admin.action(description='Mark as verified')
    def mark_verified(modeladmin, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description='Mark as unverified')
    def mark_unverified(modeladmin, request, queryset):
        queryset.update(is_verified=False)

    actions = [mark_verified, mark_unverified]


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('group', 'recipient', 'amount', 'payout_date', 'is_completed')
    list_filter = ('is_completed', 'payout_date')
    search_fields = ('group__group_name', 'recipient__username')

    @admin.action(description='Mark as completed')
    def mark_completed(modeladmin, request, queryset):
        queryset.update(is_completed=True)
        modeladmin.message_user(request, f"Marked {queryset.count()} payouts as completed")

    actions = [mark_completed]



@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('group', 'transaction_id', 'amount', 'date')
    readonly_fields = ('date',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message','notification_type', 'is_read','created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)
    actions = ['mark_as_read']

    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message

    message_short.short_description = 'Message'

    @admin.action(description='Mark as read')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)