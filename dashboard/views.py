from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from drf_spectacular.utils import extend_schema, OpenApiExample
from land.models import Project, Booking, Plots, ProjectSales, AgentSales
from land.serializers import (
    ProjectSerializer, BookingSerializer, PlotsSerializer,
    PayInstallmentSerializer, ProjectSalesSerializer, AgentSalesSerializer
)


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get dashboard statistics including total projects, plots, bookings and revenue for the authenticated user",
        summary="Dashboard Statistics"
    )
    def get(self, request):
        stats = {
            'total_projects': Project.objects.filter(user=request.user).count(),
            'total_plots': Plots.objects.filter(project__user=request.user).count(),
            'available_plots': Plots.objects.filter(project__user=request.user, is_available=True).count(),
            'sold_plots': Plots.objects.filter(project__user=request.user, is_available=False).count(),
            'total_bookings': Booking.objects.filter(plot__project__user=request.user).count(),
            'confirmed_bookings': Booking.objects.filter(plot__project__user=request.user, status='confirmed').count(),
            'pending_bookings': Booking.objects.filter(plot__project__user=request.user, status='booked').count(),
            'cancelled_bookings': Booking.objects.filter(plot__project__user=request.user, status='cancelled').count(),
            'total_revenue': Booking.objects.filter(plot__project__user=request.user, status__in=['confirmed', 'booked']).aggregate(
                total=Sum('amount_paid')
            )['total'] or 0
        }
        return Response(stats, status=status.HTTP_200_OK)


class DashboardProjectsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get all projects with plot statistics for dashboard (user's projects only)",
        summary="Dashboard Projects"
    )
    def get(self, request):
        from django.db.models import Q
        projects = Project.objects.filter(user=request.user).annotate(
            plot_count=Count('plots'),
            available_plots=Count('plots', filter=Q(plots__is_available=True)),
            sold_plots=Count('plots', filter=Q(plots__is_available=False))
        ).all()

        project_data = []
        for project in projects:
            data = ProjectSerializer(project, context={'request': request}).data
            data.update({
                'plot_count': project.plot_count,
                'available_plots': project.available_plots,
                'sold_plots': project.sold_plots
            })
            project_data.append(data)

        return Response(project_data, status=status.HTTP_200_OK)


class DashboardBookingsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingSerializer

    @extend_schema(
        description="Get all bookings for dashboard management (user's bookings only)",
        summary="Dashboard Bookings"
    )
    def get(self, request):
        bookings = Booking.objects.filter(plot__project__user=request.user).select_related('plot', 'plot__project')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardRecentActivityView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get recent bookings and projects activity for dashboard (user's data only)",
        summary="Dashboard Recent Activity"
    )
    def get(self, request):
        recent_bookings = Booking.objects.filter(plot__project__user=request.user).select_related('plot', 'plot__project').order_by('-booking_date')[:10]
        recent_projects = Project.objects.filter(user=request.user).order_by('-created_at')[:5]

        data = {
            'recent_bookings': BookingSerializer(recent_bookings, many=True).data,
            'recent_projects': ProjectSerializer(recent_projects, many=True, context={'request': request}).data
        }
        return Response(data, status=status.HTTP_200_OK)


class DashboardUpdateBookingView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingSerializer

    @extend_schema(
        responses={200: BookingSerializer},
        description="Get booking details by booking ID including balance calculation (must belong to user's projects)",
        summary="Get Single Booking"
    )
    def get(self, request, booking_id):
        try:
            booking = Booking.objects.filter(plot__project__user=request.user).select_related('plot', 'plot__project').get(id=booking_id)
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
        description="Partially update a booking. The booking must belong to one of the user's projects.",
        summary="Update Booking (Partial)"
    )
    def patch(self, request, booking_id):
        try:
            booking = Booking.objects.filter(plot__project__user=request.user).select_related('plot', 'plot__project').get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Partial update
        serializer = BookingSerializer(booking, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=BookingSerializer,
        responses={200: BookingSerializer},
        description="Fully update a booking. The booking must belong to one of the user's projects.",
        summary="Update Booking (Full)"
    )
    def put(self, request, booking_id):
        try:
            booking = Booking.objects.filter(plot__project__user=request.user).select_related('plot', 'plot__project').get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Full update
        serializer = BookingSerializer(booking, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={204: None},
        description="Delete a booking. The booking must belong to one of the user's projects. Sets the plot back to available.",
        summary="Delete Booking"
    )
    def delete(self, request, booking_id):
        try:
            booking = Booking.objects.filter(plot__project__user=request.user).select_related('plot', 'plot__project').get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Set plot back to available when booking is deleted
        plot = booking.plot
        plot.is_available = True
        plot.save()

        booking.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PayInstallmentView(APIView):
    permission_classes = [IsAuthenticated]
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
        description="Make an installment payment on a booked property. Updates booking deposit, project sales, and agent sales tracker. (booking must belong to user's projects)",
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
            # Get the booking (must belong to user's projects)
            booking = Booking.objects.filter(plot__project__user=request.user).select_related('plot', 'plot__project').get(id=booking_id)
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

        try:
            # Handle ProjectSales - check for existing record first
            from django.core.exceptions import MultipleObjectsReturned

            try:
                project_sale, created = ProjectSales.objects.update_or_create(
                    plot=booking.plot,
                    client=booking.customer_name,
                    defaults={
                        'phase': booking.phase or '',
                        'purchase_price': booking.purchase_price,
                        'deposit': booking.amount_paid
                    }
                )
            except MultipleObjectsReturned:
                # If multiple records exist, get the first one and update it
                project_sale = ProjectSales.objects.filter(
                    plot=booking.plot,
                    client=booking.customer_name
                ).first()
                project_sale.phase = booking.phase or ''
                project_sale.purchase_price = booking.purchase_price
                project_sale.deposit = booking.amount_paid
                project_sale.save()
                created = False

            # Handle AgentSales - check for existing record first
            try:
                from decimal import Decimal
                agent_sale, agent_created = AgentSales.objects.update_or_create(
                    plot=booking.plot,
                    principal_agent=agent_name,
                    defaults={
                        'phase': booking.phase or '',
                        'purchase_price': booking.purchase_price,
                        'commission': Decimal('5.00'),  # Default commission, can be customized
                        'sub_agent_name': ''
                    }
                )
            except MultipleObjectsReturned:
                # If multiple records exist, get the first one and update it
                agent_sale = AgentSales.objects.filter(
                    plot=booking.plot,
                    principal_agent=agent_name
                ).first()
                agent_sale.phase = booking.phase or ''
                agent_sale.purchase_price = booking.purchase_price
                agent_sale.save()
                agent_created = False

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
        except Exception as e:
            # Log the error and return a proper error response
            from django.conf import settings
            import traceback

            error_response = {
                'error': 'Failed to process installment payment',
                'detail': str(e)
            }

            # Only include traceback in debug mode
            if settings.DEBUG:
                error_response['traceback'] = traceback.format_exc()

            return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
