"""
Super Admin Views
Endpoints for super admins to manage and view everything in the system
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q, Avg
from datetime import datetime, timedelta

from land.models import Project, Plots, Booking, ProjectSales, AgentSales
from land.serializers import (
    ProjectSerializer, PlotsSerializer, BookingSerializer,
    ProjectSalesSerializer, AgentSalesSerializer
)
from authentication.serializers import UserSerializer


# ============ USER MANAGEMENT ============

class AdminUserListView(APIView):
    """List all users in the system"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: UserSerializer(many=True)},
        description="Get all users in the system with their details",
        summary="List All Users (Admin)"
    )
    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    """Get, update, or delete a specific user"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: UserSerializer},
        description="Get detailed information about a specific user",
        summary="Get User Details (Admin)"
    )
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user)

            # Add additional stats
            user_data = serializer.data
            user_data['stats'] = {
                'total_projects': Project.objects.filter(user=user).count(),
                'total_plots': Plots.objects.filter(project__user=user).count(),
                'total_bookings': Booking.objects.filter(plot__project__user=user).count(),
                'total_project_sales': ProjectSales.objects.filter(plot__project__user=user).count(),
                'total_agent_sales': AgentSales.objects.filter(plot__project__user=user).count(),
            }

            return Response(user_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'is_active': {'type': 'boolean'},
                    'is_staff': {'type': 'boolean'},
                    'is_superuser': {'type': 'boolean'},
                    'first_name': {'type': 'string'},
                    'last_name': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'},
                }
            }
        },
        responses={200: UserSerializer},
        description="Update user details or permissions",
        summary="Update User (Admin)"
    )
    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)

            # Update allowed fields
            if 'is_active' in request.data:
                user.is_active = request.data['is_active']
            if 'is_staff' in request.data:
                user.is_staff = request.data['is_staff']
            if 'is_superuser' in request.data:
                user.is_superuser = request.data['is_superuser']
            if 'first_name' in request.data:
                user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                user.last_name = request.data['last_name']
            if 'email' in request.data:
                user.email = request.data['email']

            user.save()
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={204: None},
        description="Delete a user and all their data",
        summary="Delete User (Admin)"
    )
    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)

            # Prevent deleting self
            if user.id == request.user.id:
                return Response(
                    {'error': 'Cannot delete your own account'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============ PROJECT MANAGEMENT ============

class AdminProjectListView(APIView):
    """List all projects in the system"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', type=int, location=OpenApiParameter.QUERY, description='Filter by user ID'),
        ],
        responses={200: ProjectSerializer(many=True)},
        description="Get all projects across all users with optional filtering",
        summary="List All Projects (Admin)"
    )
    def get(self, request):
        projects = Project.objects.select_related('user').all()

        # Optional filter by user
        user_id = request.query_params.get('user_id')
        if user_id:
            projects = projects.filter(user_id=user_id)

        projects = projects.order_by('-created_at')
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminProjectDetailView(APIView):
    """Get or delete a specific project"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: ProjectSerializer},
        description="Get detailed information about a specific project",
        summary="Get Project Details (Admin)"
    )
    def get(self, request, project_id):
        try:
            project = Project.objects.select_related('user').get(id=project_id)
            serializer = ProjectSerializer(project)

            # Add statistics
            project_data = serializer.data
            project_data['stats'] = {
                'total_plots': Plots.objects.filter(project=project).count(),
                'available_plots': Plots.objects.filter(project=project, is_available=True).count(),
                'total_bookings': Booking.objects.filter(plot__project=project).count(),
                'total_sales': ProjectSales.objects.filter(plot__project=project).count(),
            }

            return Response(project_data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={204: None},
        description="Delete a project and all its related data",
        summary="Delete Project (Admin)"
    )
    def delete(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
            project.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============ PLOTS MANAGEMENT ============

class AdminPlotsListView(APIView):
    """List all plots in the system"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='project_id', type=int, location=OpenApiParameter.QUERY, description='Filter by project ID'),
            OpenApiParameter(name='user_id', type=int, location=OpenApiParameter.QUERY, description='Filter by user ID'),
            OpenApiParameter(name='is_available', type=bool, location=OpenApiParameter.QUERY, description='Filter by availability'),
        ],
        responses={200: PlotsSerializer(many=True)},
        description="Get all plots across all users with optional filtering",
        summary="List All Plots (Admin)"
    )
    def get(self, request):
        plots = Plots.objects.select_related('project', 'project__user').all()

        # Optional filters
        project_id = request.query_params.get('project_id')
        user_id = request.query_params.get('user_id')
        is_available = request.query_params.get('is_available')

        if project_id:
            plots = plots.filter(project_id=project_id)
        if user_id:
            plots = plots.filter(project__user_id=user_id)
        if is_available is not None:
            plots = plots.filter(is_available=is_available.lower() == 'true')

        plots = plots.order_by('-created_at')
        serializer = PlotsSerializer(plots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============ BOOKINGS MANAGEMENT ============

class AdminBookingsListView(APIView):
    """List all bookings in the system"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', type=int, location=OpenApiParameter.QUERY, description='Filter by user ID'),
            OpenApiParameter(name='status', type=str, location=OpenApiParameter.QUERY, description='Filter by status'),
        ],
        responses={200: BookingSerializer(many=True)},
        description="Get all bookings across all users with optional filtering",
        summary="List All Bookings (Admin)"
    )
    def get(self, request):
        bookings = Booking.objects.select_related('plot', 'plot__project', 'plot__project__user').all()

        # Optional filters
        user_id = request.query_params.get('user_id')
        booking_status = request.query_params.get('status')

        if user_id:
            bookings = bookings.filter(plot__project__user_id=user_id)
        if booking_status:
            bookings = bookings.filter(status=booking_status)

        bookings = bookings.order_by('-booking_date')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminBookingDetailView(APIView):
    """Get or delete a specific booking"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={200: BookingSerializer},
        description="Get detailed information about a specific booking",
        summary="Get Booking Details (Admin)"
    )
    def get(self, request, booking_id):
        try:
            booking = Booking.objects.select_related('plot', 'plot__project').get(id=booking_id)
            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={204: None},
        description="Delete a booking",
        summary="Delete Booking (Admin)"
    )
    def delete(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============ SALES MANAGEMENT ============

class AdminProjectSalesListView(APIView):
    """List all project sales in the system"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', type=int, location=OpenApiParameter.QUERY, description='Filter by user ID'),
        ],
        responses={200: ProjectSalesSerializer(many=True)},
        description="Get all project sales across all users",
        summary="List All Project Sales (Admin)"
    )
    def get(self, request):
        sales = ProjectSales.objects.select_related('plot', 'plot__project', 'plot__project__user').all()

        user_id = request.query_params.get('user_id')
        if user_id:
            sales = sales.filter(plot__project__user_id=user_id)

        sales = sales.order_by('-created_at')
        serializer = ProjectSalesSerializer(sales, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminAgentSalesListView(APIView):
    """List all agent sales in the system"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', type=int, location=OpenApiParameter.QUERY, description='Filter by user ID'),
        ],
        responses={200: AgentSalesSerializer(many=True)},
        description="Get all agent sales across all users",
        summary="List All Agent Sales (Admin)"
    )
    def get(self, request):
        sales = AgentSales.objects.select_related('plot', 'plot__project', 'plot__project__user').all()

        user_id = request.query_params.get('user_id')
        if user_id:
            sales = sales.filter(plot__project__user_id=user_id)

        sales = sales.order_by('-created_at')
        serializer = AgentSalesSerializer(sales, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============ DASHBOARD & STATISTICS ============

@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'users': {'type': 'object'},
                'projects': {'type': 'object'},
                'plots': {'type': 'object'},
                'bookings': {'type': 'object'},
                'sales': {'type': 'object'},
            }
        }
    },
    description="Get comprehensive system statistics and overview",
    summary="System Dashboard (Admin)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    """
    Get system-wide statistics and dashboard data
    """

    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    new_users_30days = User.objects.filter(
        date_joined__gte=datetime.now() - timedelta(days=30)
    ).count()

    # Project statistics
    total_projects = Project.objects.count()
    projects_by_user = Project.objects.values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    # Plot statistics
    total_plots = Plots.objects.count()
    available_plots = Plots.objects.filter(is_available=True).count()
    residential_plots = Plots.objects.filter(property_type='residential').count()
    commercial_plots = Plots.objects.filter(property_type='commercial').count()

    # Booking statistics
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    pending_bookings = Booking.objects.filter(status='booked').count()
    total_booking_value = Booking.objects.aggregate(
        total=Sum('purchase_price')
    )['total'] or 0

    # Sales statistics
    total_project_sales = ProjectSales.objects.count()
    total_agent_sales = AgentSales.objects.count()
    total_sales_revenue = ProjectSales.objects.aggregate(
        total=Sum('purchase_price')
    )['total'] or 0
    total_deposits = ProjectSales.objects.aggregate(
        total=Sum('deposit')
    )['total'] or 0

    # Recent activity (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_projects = Project.objects.filter(created_at__gte=seven_days_ago).count()
    recent_bookings = Booking.objects.filter(booking_date__gte=seven_days_ago).count()
    recent_sales = ProjectSales.objects.filter(created_at__gte=seven_days_ago).count()

    return Response({
        'users': {
            'total': total_users,
            'active': active_users,
            'staff': staff_users,
            'new_last_30_days': new_users_30days,
        },
        'projects': {
            'total': total_projects,
            'recent_7_days': recent_projects,
            'top_users': list(projects_by_user),
        },
        'plots': {
            'total': total_plots,
            'available': available_plots,
            'sold': total_plots - available_plots,
            'residential': residential_plots,
            'commercial': commercial_plots,
        },
        'bookings': {
            'total': total_bookings,
            'confirmed': confirmed_bookings,
            'pending': pending_bookings,
            'total_value': float(total_booking_value),
            'recent_7_days': recent_bookings,
        },
        'sales': {
            'project_sales': total_project_sales,
            'agent_sales': total_agent_sales,
            'total_revenue': float(total_sales_revenue),
            'total_deposits': float(total_deposits),
            'outstanding': float(total_sales_revenue - total_deposits),
            'recent_7_days': recent_sales,
        },
        'system': {
            'timestamp': datetime.now().isoformat(),
            'period': 'All time',
        }
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'overview': {'type': 'object'},
                'growth': {'type': 'object'},
            }
        }
    },
    description="Get system analytics and growth trends",
    summary="System Analytics (Admin)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_analytics(request):
    """
    Get system analytics, trends, and insights
    """

    # Monthly growth trends (last 6 months)
    monthly_data = []
    for i in range(6, 0, -1):
        month_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)

        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'users': User.objects.filter(
                date_joined__gte=month_start,
                date_joined__lt=month_end
            ).count(),
            'projects': Project.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count(),
            'bookings': Booking.objects.filter(
                booking_date__gte=month_start,
                booking_date__lt=month_end
            ).count(),
            'sales': ProjectSales.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count(),
        })

    # Revenue analytics
    total_revenue = ProjectSales.objects.aggregate(Sum('purchase_price'))['purchase_price__sum'] or 0
    total_paid = ProjectSales.objects.aggregate(Sum('deposit'))['deposit__sum'] or 0
    outstanding = total_revenue - total_paid

    # Average values
    avg_project_size = Project.objects.aggregate(Avg('size'))['size__avg'] or 0
    avg_plot_price = Plots.objects.aggregate(Avg('price'))['price__avg'] or 0
    avg_sale_price = ProjectSales.objects.aggregate(Avg('purchase_price'))['purchase_price__avg'] or 0

    return Response({
        'overview': {
            'total_revenue': float(total_revenue),
            'total_paid': float(total_paid),
            'outstanding': float(outstanding),
            'collection_rate': float((total_paid / total_revenue * 100) if total_revenue > 0 else 0),
        },
        'averages': {
            'project_size': float(avg_project_size),
            'plot_price': float(avg_plot_price),
            'sale_price': float(avg_sale_price),
        },
        'growth': {
            'monthly_trends': monthly_data,
        },
        'timestamp': datetime.now().isoformat(),
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'results': {'type': 'object'},
            }
        }
    },
    parameters=[
        OpenApiParameter(name='q', type=str, location=OpenApiParameter.QUERY, description='Search query'),
    ],
    description="Search across users, projects, plots, and sales",
    summary="Global Search (Admin)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_search(request):
    """
    Global search across all entities
    """
    query = request.query_params.get('q', '')

    if not query:
        return Response({
            'error': 'Search query is required',
            'usage': 'Add ?q=search_term to your request'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Search users
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:10]

    # Search projects
    projects = Project.objects.filter(
        Q(name__icontains=query) |
        Q(location__icontains=query)
    )[:10]

    # Search plots
    plots = Plots.objects.filter(
        plot_number__icontains=query
    )[:10]

    # Search bookings
    bookings = Booking.objects.filter(
        Q(customer_name__icontains=query) |
        Q(customer_contact__icontains=query) |
        Q(payment_reference__icontains=query)
    )[:10]

    return Response({
        'query': query,
        'results': {
            'users': {
                'count': users.count(),
                'items': UserSerializer(users, many=True).data
            },
            'projects': {
                'count': projects.count(),
                'items': ProjectSerializer(projects, many=True).data
            },
            'plots': {
                'count': plots.count(),
                'items': PlotsSerializer(plots, many=True).data
            },
            'bookings': {
                'count': bookings.count(),
                'items': BookingSerializer(bookings, many=True).data
            },
        }
    }, status=status.HTTP_200_OK)
