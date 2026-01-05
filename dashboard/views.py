from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from drf_spectacular.utils import extend_schema
from land.models import Project, Booking, Plots
from land.serializers import ProjectSerializer, BookingSerializer, PlotsSerializer


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        description="Get dashboard statistics including total projects, plots, bookings and revenue",
        summary="Dashboard Statistics"
    )
    def get(self, request):
        stats = {
            'total_projects': Project.objects.count(),
            'total_plots': Plots.objects.count(),
            'available_plots': Plots.objects.filter(is_available=True).count(),
            'sold_plots': Plots.objects.filter(is_available=False).count(),
            'total_bookings': Booking.objects.count(),
            'confirmed_bookings': Booking.objects.filter(status='confirmed').count(),
            'pending_bookings': Booking.objects.filter(status='booked').count(),
            'cancelled_bookings': Booking.objects.filter(status='cancelled').count(),
            'total_revenue': Booking.objects.filter(status__in=['confirmed', 'booked']).aggregate(
                total=Sum('amount_paid')
            )['total'] or 0
        }
        return Response(stats, status=status.HTTP_200_OK)


class DashboardProjectsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        description="Get all projects with plot statistics for dashboard",
        summary="Dashboard Projects"
    )
    def get(self, request):
        from django.db.models import Q
        projects = Project.objects.annotate(
            plot_count=Count('plots'),
            available_plots=Count('plots', filter=Q(plots__is_available=True)),
            sold_plots=Count('plots', filter=Q(plots__is_available=False))
        ).all()
        
        project_data = []
        for project in projects:
            data = ProjectSerializer(project).data
            data.update({
                'plot_count': project.plot_count,
                'available_plots': project.available_plots,
                'sold_plots': project.sold_plots
            })
            project_data.append(data)
        
        return Response(project_data, status=status.HTTP_200_OK)


class DashboardBookingsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        description="Get all bookings for dashboard management",
        summary="Dashboard Bookings"
    )
    def get(self, request):
        bookings = Booking.objects.select_related('plot', 'plot__project').all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardRecentActivityView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        description="Get recent bookings and projects activity for dashboard",
        summary="Dashboard Recent Activity"
    )
    def get(self, request):
        recent_bookings = Booking.objects.select_related('plot', 'plot__project').order_by('-booking_date')[:10]
        recent_projects = Project.objects.order_by('-created_at')[:5]
        
        data = {
            'recent_bookings': BookingSerializer(recent_bookings, many=True).data,
            'recent_projects': ProjectSerializer(recent_projects, many=True).data
        }
        return Response(data, status=status.HTTP_200_OK)
