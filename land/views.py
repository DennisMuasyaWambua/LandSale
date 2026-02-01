from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from land.models import Project, Booking, Plots
from land.serializers import ProjectSerializer, BookingSerializer, PlotsSerializer
# Create your views here.
class ProjectView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ProjectSerializer

    def post(self, request):
        data = request.data
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():

            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    def get(self, request):
        project = Project.objects.all()
        serializer =    ProjectSerializer(project, many=True)
        return Response(serializer.data, status=200)


class ProjectDetailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ProjectSerializer

    @extend_schema(
        responses={200: ProjectSerializer},
        description="Get a single project by ID with all project details",
        summary="Get Project"
    )
    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=404
            )

        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=200)
class BookingView(APIView):
      permission_classes = [AllowAny]
      serializer_class = BookingSerializer
      
      def post(self, request):
            data = request.data
            serializer = BookingSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
      @extend_schema(
            responses={200: BookingSerializer(many=True)},
            description="Get all bookings with plot details including phase, balance calculation, and nested project information",
            summary="List All Bookings"
      )
      def get(self, request):
            bookings = Booking.objects.all()
            serializer = BookingSerializer(bookings, many=True)
            return Response(serializer.data, status=200)
class PlotsView(APIView):
      permission_classes = [AllowAny]
      serializer_class = PlotsSerializer
      
      def get(self, request):
            plots = Plots.objects.all()
            serializer = PlotsSerializer(plots, many=True)
            return Response(serializer.data, status=200)
      def post(self, request):
            data = request.data
            serializer = PlotsSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)