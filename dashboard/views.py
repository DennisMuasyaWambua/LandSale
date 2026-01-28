from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum
from drf_spectacular.utils import extend_schema
from land.models import Project, Booking, Plots
from land.serializers import ProjectSerializer, BookingSerializer, PlotsSerializer


class DashboardStatsView(APIView):
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
    serializer_class = BookingSerializer

    @extend_schema(
        description="Get all bookings for dashboard management",
        summary="Dashboard Bookings"
    )
    def get(self, request):
        bookings = Booking.objects.select_related('plot', 'plot__project').all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardRecentActivityView(APIView):
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


class DashboardUpdateBookingView(APIView):
    serializer_class = BookingSerializer

    @extend_schema(
        responses={200: BookingSerializer},
        description="Get booking details by booking ID including balance calculation",
        summary="Get Single Booking"
    )
    def get(self, request, booking_id):
        try:
            booking = Booking.objects.select_related('plot', 'plot__project').get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=BookingSerializer,
        responses={200: BookingSerializer},
        description="Update booking details by booking ID (partial update - only provided fields will be updated)",
        summary="Update Booking (Partial)"
    )
    def patch(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BookingSerializer(booking, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=BookingSerializer,
        responses={200: BookingSerializer},
        description="Fully update booking details by booking ID (all fields required)",
        summary="Update Booking (Full)"
    )
    def put(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BookingSerializer(booking, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
