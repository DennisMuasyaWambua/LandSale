from super_admin.models import AuditLog
from django.utils import timezone


class AuditLogger:
    """
    Utility for creating audit log entries
    """

    @staticmethod
    def log(user, action, resource_type, description,
            resource_id=None, changes=None, metadata=None,
            request=None, was_successful=True, error_message=''):
        """
        Create an audit log entry

        Args:
            user: User performing the action
            action: Action type (create/read/update/delete/etc.)
            resource_type: Type of resource affected
            description: Human-readable description
            resource_id: ID of the affected resource
            changes: Dict of before/after values
            metadata: Additional context data
            request: Django request object
            was_successful: Whether action succeeded
            error_message: Error message if action failed
        """
        ip_address = None
        user_agent = ''

        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        log_entry = AuditLog.objects.create(
            user=user,
            username=user.username if user else 'System',
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else '',
            description=description,
            changes=changes or {},
            metadata=metadata or {},
            was_successful=was_successful,
            error_message=error_message
        )

        return log_entry

    @staticmethod
    def log_model_change(user, action, instance, changes=None, request=None):
        """
        Log changes to a model instance

        Args:
            user: User performing the action
            action: Action type (create/update/delete)
            instance: Model instance being changed
            changes: Dict of field changes
            request: Django request object
        """
        # Map model names to resource types
        resource_type_map = {
            'User': 'user',
            'Project': 'project',
            'Plots': 'plot',
            'Booking': 'booking',
            'ProjectSales': 'sale',
            'AgentSales': 'sale',
            'Payment': 'payment',
            'UserSubscription': 'subscription',
            'SubscriptionPlan': 'subscription_plan',
            'SystemSetting': 'system_setting',
            'AdminRole': 'admin_role',
        }

        model_name = instance.__class__.__name__
        resource_type = resource_type_map.get(model_name, 'unknown')

        description = f"{action.title()} {model_name} #{instance.pk}"

        return AuditLogger.log(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=instance.pk,
            description=description,
            changes=changes,
            request=request
        )
