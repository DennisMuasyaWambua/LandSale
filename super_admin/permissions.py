from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Full system access - can do everything
    """
    message = "Super admin access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Django superuser always has access
        if request.user.is_superuser:
            return True

        # Check for super_admin role
        try:
            return request.user.admin_profile.has_role('super_admin')
        except:
            return False


class IsContentAdmin(BasePermission):
    """
    Can manage projects, plots, bookings (read/write)
    """
    message = "Content admin access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        try:
            profile = request.user.admin_profile
            return (profile.has_role('super_admin') or
                   profile.has_role('content_admin'))
        except:
            return False


class IsFinanceAdmin(BasePermission):
    """
    Can manage payments, subscriptions, plans (read/write)
    """
    message = "Finance admin access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        try:
            profile = request.user.admin_profile
            return (profile.has_role('super_admin') or
                   profile.has_role('finance_admin'))
        except:
            return False


class IsSupportAdmin(BasePermission):
    """
    Read-only access with limited actions
    """
    message = "Support admin access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        try:
            profile = request.user.admin_profile
            return (profile.has_role('super_admin') or
                   profile.has_role('content_admin') or
                   profile.has_role('finance_admin') or
                   profile.has_role('support_admin'))
        except:
            return False


class CanExportData(BasePermission):
    """
    Can export data to CSV/Excel
    """
    message = "Data export permission required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        try:
            profile = request.user.admin_profile
            for role in profile.roles.all():
                if role.can_export_data:
                    return True
            return False
        except:
            return False


class CanViewAuditLogs(BasePermission):
    """
    Can view audit logs
    """
    message = "Audit log view permission required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        try:
            profile = request.user.admin_profile
            for role in profile.roles.all():
                if role.can_view_audit_logs:
                    return True
            return False
        except:
            return False
