from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.postgres.fields import ArrayField
import json


class AdminRole(models.Model):
    """
    Extended role model that wraps Django Groups with additional metadata
    """
    ROLE_TYPES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('content_admin', 'Content Admin'),
        ('finance_admin', 'Finance Admin'),
        ('support_admin', 'Support Admin'),
    ]

    role_type = models.CharField(max_length=50, choices=ROLE_TYPES, unique=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='admin_role')
    description = models.TextField(blank=True)

    # Additional role metadata
    can_access_dashboard = models.BooleanField(default=True)
    can_export_data = models.BooleanField(default=False)
    can_view_audit_logs = models.BooleanField(default=False)
    api_rate_limit = models.IntegerField(default=1000, help_text="API calls per hour")

    # Accessible modules (JSON array)
    accessible_modules = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="List of modules: users, projects, plots, bookings, sales, payments, subscriptions, settings"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['role_type']

    def __str__(self):
        return f"{self.get_role_type_display()}"


class UserAdminProfile(models.Model):
    """
    Tracks admin-specific user information and role assignments
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    roles = models.ManyToManyField(AdminRole, related_name='users', blank=True)

    # Additional admin metadata
    is_admin_active = models.BooleanField(default=True)
    admin_notes = models.TextField(blank=True)
    last_admin_login = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_role(self, role_type):
        """Check if user has a specific admin role"""
        return self.roles.filter(role_type=role_type).exists()

    def get_permissions(self):
        """Get all permissions from all assigned roles"""
        permissions = set()
        for role in self.roles.all():
            permissions.update(role.group.permissions.all())
        return list(permissions)

    def __str__(self):
        return f"Admin Profile: {self.user.username}"


class AuditLog(models.Model):
    """
    Comprehensive audit trail for all admin actions
    """
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('bulk_operation', 'Bulk Operation'),
        ('settings_change', 'Settings Change'),
        ('role_change', 'Role Change'),
    ]

    RESOURCE_TYPES = [
        ('user', 'User'),
        ('project', 'Project'),
        ('plot', 'Plot'),
        ('booking', 'Booking'),
        ('sale', 'Sale'),
        ('payment', 'Payment'),
        ('subscription', 'Subscription'),
        ('subscription_plan', 'Subscription Plan'),
        ('system_setting', 'System Setting'),
        ('admin_role', 'Admin Role'),
    ]

    # Who
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    username = models.CharField(max_length=150, help_text="Snapshot of username")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # What
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES)
    resource_id = models.CharField(max_length=100, blank=True, help_text="ID of affected resource")

    # Details
    description = models.TextField(help_text="Human-readable description")
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Before/after values: {field: {old: '', new: ''}}"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data"
    )

    # When
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Status
    was_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.username} - {self.action} {self.resource_type} at {self.timestamp}"


class SystemSetting(models.Model):
    """
    System-wide configuration settings with type safety
    """
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('email', 'Email'),
        ('url', 'URL'),
    ]

    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('email', 'Email Configuration'),
        ('payment', 'Payment Settings'),
        ('features', 'Feature Flags'),
        ('security', 'Security'),
        ('notifications', 'Notifications'),
        ('api', 'API Configuration'),
    ]

    key = models.CharField(max_length=200, unique=True, db_index=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')

    description = models.TextField(blank=True, help_text="Description of this setting")
    is_public = models.BooleanField(default=False, help_text="Can non-admin users read this?")
    is_editable = models.BooleanField(default=True, help_text="Can this be edited via API?")

    # Validation
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON rules: {min: 0, max: 100, regex: '...', choices: []}"
    )

    # Audit
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='settings_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='settings_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['key']),
        ]

    def get_typed_value(self):
        """Return value in correct type"""
        if self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes']
        elif self.setting_type == 'json':
            return json.loads(self.value)
        else:
            return self.value

    def set_typed_value(self, value):
        """Set value with type conversion"""
        if self.setting_type == 'json':
            self.value = json.dumps(value)
        elif self.setting_type == 'boolean':
            self.value = str(bool(value)).lower()
        else:
            self.value = str(value)

    def __str__(self):
        return f"{self.category}: {self.key}"


class EmailTemplate(models.Model):
    """
    Customizable email templates for system notifications
    """
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('password_reset', 'Password Reset'),
        ('subscription_success', 'Subscription Success'),
        ('subscription_expiring', 'Subscription Expiring'),
        ('payment_success', 'Payment Success'),
        ('payment_failed', 'Payment Failed'),
        ('custom', 'Custom Template'),
    ]

    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=500)
    body_html = models.TextField(help_text="HTML body with {{variable}} placeholders")
    body_text = models.TextField(help_text="Plain text fallback")

    # Available variables for this template
    available_variables = models.JSONField(
        default=list,
        help_text="List of available variables: ['user_name', 'amount', etc.]"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_template_type_display()}"
