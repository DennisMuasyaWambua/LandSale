from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
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
        serializer = ProjectSerializer(data=data)
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
        # Get projects that belong to the user or have no user assigned (legacy data)
        projects = Project.objects.filter(user=request.user) | Project.objects.filter(user__isnull=True)

        # Assign unassigned projects to the current user
        unassigned_projects = Project.objects.filter(user__isnull=True)
        if unassigned_projects.exists():
            unassigned_projects.update(user=request.user)
            # Refresh the queryset after update
            projects = Project.objects.filter(user=request.user)

        serializer = ProjectSerializer(projects, many=True)
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
            # Try to get project by ID first
            project = Project.objects.get(id=project_id)

            # Check if project has no user assigned (legacy data)
            if project.user is None:
                # Assign to current user
                project.user = request.user
                project.save()
            # Check if project belongs to the authenticated user
            elif project.user != request.user:
                return Response(
                    {'error': 'Project not found'},
                    status=404
                )

        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=404
            )

        serializer = ProjectSerializer(project)
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