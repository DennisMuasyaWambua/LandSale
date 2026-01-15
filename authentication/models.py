from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from datetime import timedelta
from decimal import Decimal

# Create your models here.

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Password reset for {self.user.username}"


class SubscriptionPlan(models.Model):
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    period_count = models.IntegerField(default=1, help_text="Number of periods (e.g., 3 months)")
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list, blank=True, help_text="List of features included in this plan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.amount} per {self.period_count} {self.period}"

    def get_duration_in_days(self):
        period_days = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365,
        }
        return period_days.get(self.period, 30) * self.period_count

    class Meta:
        ordering = ['amount']


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)

    # Recurring payment tracking
    recurring_payment_active = models.BooleanField(default=False, help_text="Whether user has active recurring payment configured at Pesapal")
    last_recurring_payment_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'} - {self.status}"

    def is_active(self):
        """Check if subscription is currently active with real-time validation and immediate expiration"""
        if self.status == 'active' and self.end_date:
            # Immediate check - if expired, auto-update status
            if timezone.now() >= self.end_date:
                self.status = 'expired'
                self.save()
                return False
            return True
        return False

    def activate_subscription(self):
        self.status = 'active'
        self.start_date = timezone.now()
        if self.plan:
            self.end_date = timezone.now() + timedelta(days=self.plan.get_duration_in_days())
        self.save()

    def cancel_subscription(self):
        self.status = 'cancelled'
        self.auto_renew = False
        self.save()

    def check_and_update_status(self):
        if self.status == 'active' and self.end_date and timezone.now() >= self.end_date:
            self.status = 'expired'
            self.save()

    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('renewal', 'Renewal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='subscription')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Pesapal transaction tracking
    pesapal_order_tracking_id = models.CharField(max_length=200, blank=True, help_text="Pesapal OrderTrackingId")
    pesapal_merchant_reference = models.CharField(max_length=200, blank=True, help_text="Our internal reference")
    pesapal_transaction_id = models.CharField(max_length=200, blank=True, null=True, help_text="Pesapal transaction ID after completion")

    # Recurring payment tracking
    is_recurring = models.BooleanField(default=False, help_text="Whether this is a recurring payment setup")
    recurring_frequency = models.CharField(max_length=20, blank=True, null=True,
        choices=[('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly'), ('YEARLY', 'Yearly')])
    recurring_start_date = models.DateField(blank=True, null=True)
    recurring_end_date = models.DateField(blank=True, null=True)

    payment_method = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=10, default='KES')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"

    class Meta:
        ordering = ['-created_at']
