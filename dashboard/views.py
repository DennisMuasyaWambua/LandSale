from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum
from drf_spectacular.utils import extend_schema, OpenApiExample
from land.models import Project, Booking, Plots, ProjectSales, AgentSales
from land.serializers import (
    ProjectSerializer, BookingSerializer, PlotsSerializer,
    PayInstallmentSerializer, ProjectSalesSerializer, AgentSalesSerializer
)


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


class PayInstallmentView(APIView):
    serializer_class = PayInstallmentSerializer

    @extend_schema(
        request=PayInstallmentSerializer,
        responses={200: {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "booking": {"type": "object"},
                "project_sales": {"type": "object"},
                "agent_sales": {"type": "object"},
                "previous_deposit": {"type": "number"},
                "new_deposit": {"type": "number"},
                "balance": {"type": "number"}
            }
        }},
        description="Make an installment payment on a booked property. Updates booking deposit, project sales, and agent sales tracker.",
        summary="Pay Installment",
        examples=[
            OpenApiExample(
                "Pay Installment Example",
                value={
                    "booking_id": 1,
                    "agent_name": "John Doe",
                    "amount": 10000
                }
            )
        ]
    )
    def post(self, request):
        serializer = PayInstallmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        booking_id = serializer.validated_data['booking_id']
        agent_name = serializer.validated_data['agent_name']
        payment_amount = serializer.validated_data['amount']

        try:
            # Get the booking
            booking = Booking.objects.select_related('plot', 'plot__project').get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Store previous deposit
        previous_deposit = booking.amount_paid

        # Update booking deposit by adding the new payment amount
        booking.amount_paid = booking.amount_paid + payment_amount
        booking.save()

        # Calculate new balance
        new_balance = booking.purchase_price - booking.amount_paid

        # Update or create ProjectSales record
        project_sale, created = ProjectSales.objects.get_or_create(
            plot=booking.plot,
            client=booking.customer_name,
            defaults={
                'phase': booking.phase or '',
                'purchase_price': booking.purchase_price,
                'deposit': booking.amount_paid
            }
        )

        if not created:
            # Update existing project sale
            project_sale.deposit = booking.amount_paid
            project_sale.save()

        # Update or create AgentSales record
        agent_sale, agent_created = AgentSales.objects.get_or_create(
            plot=booking.plot,
            principal_agent=agent_name,
            defaults={
                'phase': booking.phase or '',
                'purchase_price': booking.purchase_price,
                'commission': 5.00,  # Default commission, can be customized
                'sub_agent_name': ''
            }
        )

        if not agent_created:
            # Update existing agent sale
            agent_sale.purchase_price = booking.purchase_price
            agent_sale.save()

        # Prepare response
        return Response({
            'message': 'Installment payment processed successfully',
            'booking': BookingSerializer(booking).data,
            'project_sales': ProjectSalesSerializer(project_sale).data,
            'agent_sales': AgentSalesSerializer(agent_sale).data,
            'previous_deposit': float(previous_deposit),
            'new_deposit': float(booking.amount_paid),
            'payment_made': float(payment_amount),
            'balance': float(new_balance)
        }, status=status.HTTP_200_OK)
