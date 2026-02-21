from django.db.models import Q


def get_user_projects_filter(user):
    """
    Returns Q object for filtering projects based on user type.

    - Admin/super_admin: Returns projects they own (Q(user=user))
    - Client/subagent: Returns projects they're assigned to (via ProjectAssignment)
    - Others: Returns no projects (Q(id=-1))

    Usage:
        projects = Project.objects.filter(get_user_projects_filter(request.user))
        plots = Plots.objects.filter(get_user_projects_filter(request.user))
    """
    from land.models import ProjectAssignment

    # Check if user has profile
    if not hasattr(user, 'profile'):
        # No profile means old user or not authenticated properly
        # Fallback: check if they own any projects
        from land.models import Project
        if Project.objects.filter(user=user).exists():
            return Q(user=user)
        return Q(id=-1)  # No access

    user_type = user.profile.user_type

    # Admin/super_admin: their owned projects
    if user_type in ['admin', 'super_admin']:
        return Q(user=user)

    # Client/subagent: assigned projects
    elif user_type in ['client', 'subagent']:
        assigned_project_ids = ProjectAssignment.objects.filter(
            user=user
        ).values_list('project_id', flat=True)
        return Q(id__in=assigned_project_ids)

    # Unknown user type: no access
    return Q(id=-1)


def get_user_plots_filter(user):
    """
    Returns Q object for filtering plots based on user type.

    Plots are filtered by the projects the user has access to.

    Usage:
        plots = Plots.objects.filter(get_user_plots_filter(request.user))
    """
    # Get project filter and apply to plot's project
    project_filter = get_user_projects_filter(user)

    # Transform project filter to apply to plot.project
    # Q(user=user) becomes Q(project__user=user)
    # Q(id__in=list) becomes Q(project__id__in=list)

    if not hasattr(user, 'profile'):
        # Fallback for users without profile
        from land.models import Project
        if Project.objects.filter(user=user).exists():
            return Q(project__user=user)
        return Q(id=-1)

    user_type = user.profile.user_type

    if user_type in ['admin', 'super_admin']:
        return Q(project__user=user)
    elif user_type in ['client', 'subagent']:
        from land.models import ProjectAssignment
        assigned_project_ids = ProjectAssignment.objects.filter(
            user=user
        ).values_list('project_id', flat=True)
        return Q(project__id__in=assigned_project_ids)

    return Q(id=-1)


def get_user_bookings_filter(user):
    """
    Returns Q object for filtering bookings based on user type.

    - Admin/super_admin: Bookings from their projects (Q(plot__project__user=user))
    - Client/subagent: Their own bookings (Q(user=user))

    Usage:
        bookings = Booking.objects.filter(get_user_bookings_filter(request.user))
    """
    if not hasattr(user, 'profile'):
        # Fallback: show bookings from owned projects
        return Q(plot__project__user=user)

    user_type = user.profile.user_type

    # Admin/super_admin: bookings from their projects
    if user_type in ['admin', 'super_admin']:
        return Q(plot__project__user=user)

    # Client/subagent: their own bookings only
    elif user_type in ['client', 'subagent']:
        return Q(user=user)

    return Q(id=-1)
