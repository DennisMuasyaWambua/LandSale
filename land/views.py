from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from land.models import Project, Booking, Plots
from land.serializers import ProjectSerializer, BookingSerializer, PlotsSerializer
# Create your views here.
class ProjectView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer

    @extend_schema(
        request=ProjectSerializer,
        responses={201: ProjectSerializer},
        description="Create a new project for the authenticated user",
        summary="Create Project"
    )
    def post(self, request):
        data = request.data
        serializer = ProjectSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @extend_schema(
        responses={200: ProjectSerializer(many=True)},
        description="Get all projects for the authenticated user",
        summary="List User Projects"
    )
    def get(self, request):
        # Get only projects that belong to the authenticated user
        projects = Project.objects.filter(user=request.user)
        serializer = ProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data, status=200)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer

    @extend_schema(
        responses={200: ProjectSerializer},
        description="Get a single project by ID. Users can only access their own projects.",
        summary="Get Project"
    )
    def get(self, request, project_id):
        try:
            # Get project only if it belongs to the authenticated user
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=404
            )

        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data, status=200)
class BookingView(APIView):
      permission_classes = [IsAuthenticated]
      serializer_class = BookingSerializer

      @extend_schema(
            request=BookingSerializer,
            responses={201: BookingSerializer},
            description="Create a new booking. The plot must belong to one of the user's projects.",
            summary="Create Booking"
      )
      def post(self, request):
            data = request.data
            # Set status to 'booked' if not provided
            if 'status' not in data:
                data['status'] = 'booked'
            serializer = BookingSerializer(data=data)
            if serializer.is_valid():
                # Validate that the plot belongs to user's project
                plot = serializer.validated_data.get('plot')
                if plot and plot.project.user != request.user:
                    return Response(
                        {'error': 'You can only create bookings for plots in your own projects'},
                        status=403
                    )
                serializer.save()
                # Set plot as unavailable when booking is created
                plot.is_available = False
                plot.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)

      @extend_schema(
            responses={200: BookingSerializer(many=True)},
            description="Get all bookings for the authenticated user's projects with plot details including phase, balance calculation, and nested project information",
            summary="List User's Bookings"
      )
      def get(self, request):
            bookings = Booking.objects.filter(plot__project__user=request.user)
            serializer = BookingSerializer(bookings, many=True)
            return Response(serializer.data, status=200)


class BookingUpdateView(APIView):
      permission_classes = [IsAuthenticated]
      serializer_class = BookingSerializer

      @extend_schema(
            responses={200: BookingSerializer},
            description="Get a specific booking by ID. The booking must belong to one of the user's projects.",
            summary="Get Booking Details"
      )
      def get(self, request, booking_id):
            try:
                # Get booking only if it belongs to user's projects
                booking = Booking.objects.filter(plot__project__user=request.user).get(id=booking_id)
                serializer = BookingSerializer(booking)
                return Response(serializer.data, status=200)
            except Booking.DoesNotExist:
                return Response(
                    {'error': 'Booking not found'},
                    status=404
                )

      @extend_schema(
            request=BookingSerializer,
            responses={200: BookingSerializer},
            description="Update a booking (partial or full). The booking must belong to one of the user's projects.",
            summary="Update Booking"
      )
      def patch(self, request, booking_id):
            try:
                # Get booking only if it belongs to user's projects
                booking = Booking.objects.filter(plot__project__user=request.user).get(id=booking_id)
            except Booking.DoesNotExist:
                return Response(
                    {'error': 'Booking not found'},
                    status=404
                )

            # Partial update
            serializer = BookingSerializer(booking, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)

      @extend_schema(
            request=BookingSerializer,
            responses={200: BookingSerializer},
            description="Update a booking (full replacement). The booking must belong to one of the user's projects.",
            summary="Replace Booking"
      )
      def put(self, request, booking_id):
            try:
                # Get booking only if it belongs to user's projects
                booking = Booking.objects.filter(plot__project__user=request.user).get(id=booking_id)
            except Booking.DoesNotExist:
                return Response(
                    {'error': 'Booking not found'},
                    status=404
                )

            # Full update
            serializer = BookingSerializer(booking, data=request.data, partial=False)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)

      @extend_schema(
            responses={204: None},
            description="Delete a booking. The booking must belong to one of the user's projects.",
            summary="Delete Booking"
      )
      def delete(self, request, booking_id):
            try:
                # Get booking only if it belongs to user's projects
                booking = Booking.objects.filter(plot__project__user=request.user).get(id=booking_id)

                # Set plot back to available when booking is deleted
                plot = booking.plot
                plot.is_available = True
                plot.save()

                booking.delete()
                return Response(status=204)
            except Booking.DoesNotExist:
                return Response(
                    {'error': 'Booking not found'},
                    status=404
                )


class PlotsView(APIView):
      permission_classes = [IsAuthenticated]
      serializer_class = PlotsSerializer

      @extend_schema(
            responses={200: PlotsSerializer(many=True)},
            description="Get all plots for the authenticated user's projects",
            summary="List User's Plots"
      )
      def get(self, request):
            plots = Plots.objects.filter(project__user=request.user)
            serializer = PlotsSerializer(plots, many=True)
            return Response(serializer.data, status=200)

      @extend_schema(
            request=PlotsSerializer,
            responses={201: PlotsSerializer},
            description="Create a new plot. The project must belong to the authenticated user.",
            summary="Create Plot"
      )
      def post(self, request):
            data = request.data
            serializer = PlotsSerializer(data=data)
            if serializer.is_valid():
                # Validate that the project belongs to the user
                project = serializer.validated_data.get('project')
                if project and project.user != request.user:
                    return Response(
                        {'error': 'You can only create plots for your own projects'},
                        status=403
                    )
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)

