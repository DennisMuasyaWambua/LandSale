from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def require_admin_role(*allowed_roles):
    """
    Decorator to require specific admin roles
    Usage: @require_admin_role('super_admin', 'content_admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if request.user.is_superuser:
                return view_func(self, request, *args, **kwargs)

            try:
                profile = request.user.admin_profile
                has_role = any(profile.has_role(role) for role in allowed_roles)

                if not has_role:
                    return Response(
                        {'error': f'Required role: {", ".join(allowed_roles)}'},
                        status=status.HTTP_403_FORBIDDEN
                    )

                return view_func(self, request, *args, **kwargs)
            except:
                return Response(
                    {'error': 'Admin access required'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return wrapper
    return decorator


def audit_action(action, resource_type):
    """
    Decorator to automatically audit API actions
    Usage: @audit_action('update', 'user')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Import here to avoid circular imports
            from super_admin.utils.audit_logger import AuditLogger

            # Execute the view
            response = view_func(self, request, *args, **kwargs)

            # Log successful actions (2xx status codes)
            if 200 <= response.status_code < 300:
                resource_id = (
                    kwargs.get('pk') or
                    kwargs.get('id') or
                    kwargs.get('user_id') or
                    kwargs.get('project_id') or
                    kwargs.get('plot_id') or
                    kwargs.get('booking_id') or
                    kwargs.get('sale_id') or
                    kwargs.get('plan_id') or
                    kwargs.get('role_id') or
                    ''
                )

                AuditLogger.log(
                    user=request.user,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    description=f"{action.title()} {resource_type}",
                    metadata={'endpoint': request.path, 'method': request.method},
                    request=request,
                    was_successful=True
                )

            return response
        return wrapper
    return decorator
