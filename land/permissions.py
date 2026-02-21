from rest_framework.permissions import BasePermission


class IsAdminUserType(BasePermission):
    """
    User has admin or super_admin user_type.
    This is for project owners who manage their properties.
    """
    message = "Admin access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Django superuser always has access
        if request.user.is_superuser:
            return True

        # Check user_type via UserProfile
        try:
            return request.user.profile.user_type in ['admin', 'super_admin']
        except:
            # No profile or error - deny access
            return False


class IsClientOrSubagent(BasePermission):
    """
    User is a client or subagent.
    These users can view assigned projects and create bookings.
    """
    message = "Client or subagent access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Check user_type via UserProfile
        try:
            return request.user.profile.user_type in ['client', 'subagent']
        except:
            return False


class CanAccessProject(BasePermission):
    """
    User can access the project (owner, assigned client/subagent, or super admin).
    This is an object-level permission.
    """
    message = "You don't have access to this project."

    def has_object_permission(self, request, view, obj):
        # obj is a Project instance
        user = request.user

        if not user.is_authenticated:
            return False

        # Superuser has access to everything
        if user.is_superuser:
            return True

        # Project owner (admin)
        if obj.user == user:
            return True

        # Assigned client/subagent
        from land.models import ProjectAssignment
        if ProjectAssignment.objects.filter(user=user, project=obj).exists():
            return True

        return False


class CanCreateBooking(BasePermission):
    """
    User can create bookings.
    - Admins can create bookings for their projects
    - Clients/subagents can create bookings for assigned projects (with 'book' permission)
    """
    message = "You don't have permission to create bookings."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # All authenticated users with profiles can attempt to create bookings
        # The actual project access check happens in the view logic
        return hasattr(request.user, 'profile')


class CanViewBooking(BasePermission):
    """
    User can view a specific booking.
    - Admins can view bookings from their projects
    - Clients/subagents can view their own bookings
    """
    message = "You don't have access to this booking."

    def has_object_permission(self, request, view, obj):
        # obj is a Booking instance
        user = request.user

        if not user.is_authenticated:
            return False

        # Superuser has access to everything
        if user.is_superuser:
            return True

        # Check user type
        try:
            user_type = user.profile.user_type

            # Admin: can view bookings from their projects
            if user_type in ['admin', 'super_admin']:
                return obj.plot.project.user == user

            # Client/subagent: can only view their own bookings
            elif user_type in ['client', 'subagent']:
                return obj.user == user

        except:
            pass

        return False


class CanManageProjectAssignments(BasePermission):
    """
    User can manage project assignments (assign users to projects).
    Only admins and super_admins can do this.
    """
    message = "Admin access required to manage project assignments."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        try:
            return request.user.profile.user_type in ['admin', 'super_admin']
        except:
            return False
