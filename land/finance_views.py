from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from land.models import ProjectSales, AgentSales
from land.serializers import ProjectSalesSerializer, AgentSalesSerializer


class ProjectSalesListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSalesSerializer

    @extend_schema(
        responses={200: ProjectSalesSerializer(many=True)},
        description="Get all project sales records for the authenticated user's projects with plot and balance details",
        summary="List User's Project Sales"
    )
    def get(self, request):
        project_sales = ProjectSales.objects.select_related('plot', 'plot__project').filter(plot__project__user=request.user)
        serializer = ProjectSalesSerializer(project_sales, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ProjectSalesSerializer,
        responses={201: ProjectSalesSerializer},
        description="Create a new project sales record. The plot must belong to one of the user's projects.",
        summary="Create Project Sale"
    )
    def post(self, request):
        serializer = ProjectSalesSerializer(data=request.data)
        if serializer.is_valid():
            # Validate that the plot belongs to user's project
            plot = serializer.validated_data.get('plot')
            if plot and plot.project.user != request.user:
                return Response(
                    {'error': 'You can only create project sales for plots in your own projects'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectSalesDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSalesSerializer

    @extend_schema(
        responses={200: ProjectSalesSerializer},
        description="Get a single project sales record by ID. The record must belong to one of the user's projects.",
        summary="Get Project Sale"
    )
    def get(self, request, sale_id):
        try:
            project_sale = ProjectSales.objects.select_related('plot', 'plot__project').get(
                id=sale_id,
                plot__project__user=request.user
            )
        except ProjectSales.DoesNotExist:
            return Response(
                {'error': 'Project sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProjectSalesSerializer(project_sale)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ProjectSalesSerializer,
        responses={200: ProjectSalesSerializer},
        description="Partially update a project sales record. The record must belong to one of the user's projects.",
        summary="Update Project Sale (Partial)"
    )
    def patch(self, request, sale_id):
        try:
            project_sale = ProjectSales.objects.get(id=sale_id, plot__project__user=request.user)
        except ProjectSales.DoesNotExist:
            return Response(
                {'error': 'Project sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProjectSalesSerializer(project_sale, data=request.data, partial=True)
        if serializer.is_valid():
            # Validate plot change if provided
            plot = serializer.validated_data.get('plot')
            if plot and plot.project.user != request.user:
                return Response(
                    {'error': 'You can only assign plots from your own projects'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=ProjectSalesSerializer,
        responses={200: ProjectSalesSerializer},
        description="Fully update a project sales record. The record must belong to one of the user's projects.",
        summary="Update Project Sale (Full)"
    )
    def put(self, request, sale_id):
        try:
            project_sale = ProjectSales.objects.get(id=sale_id, plot__project__user=request.user)
        except ProjectSales.DoesNotExist:
            return Response(
                {'error': 'Project sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProjectSalesSerializer(project_sale, data=request.data)
        if serializer.is_valid():
            # Validate plot
            plot = serializer.validated_data.get('plot')
            if plot and plot.project.user != request.user:
                return Response(
                    {'error': 'You can only assign plots from your own projects'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={204: None},
        description="Delete a project sales record. The record must belong to one of the user's projects.",
        summary="Delete Project Sale"
    )
    def delete(self, request, sale_id):
        try:
            project_sale = ProjectSales.objects.get(id=sale_id, plot__project__user=request.user)
        except ProjectSales.DoesNotExist:
            return Response(
                {'error': 'Project sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        project_sale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentSalesListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AgentSalesSerializer

    @extend_schema(
        responses={200: AgentSalesSerializer(many=True)},
        description="Get all agent sales records for the authenticated user's projects with plot, commission, and agent details",
        summary="List User's Agent Sales"
    )
    def get(self, request):
        agent_sales = AgentSales.objects.select_related('plot', 'plot__project').filter(plot__project__user=request.user)
        serializer = AgentSalesSerializer(agent_sales, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=AgentSalesSerializer,
        responses={201: AgentSalesSerializer},
        description="Create a new agent sales record. The plot must belong to one of the user's projects.",
        summary="Create Agent Sale"
    )
    def post(self, request):
        serializer = AgentSalesSerializer(data=request.data)
        if serializer.is_valid():
            # Validate that the plot belongs to user's project
            plot = serializer.validated_data.get('plot')
            if plot and plot.project.user != request.user:
                return Response(
                    {'error': 'You can only create agent sales for plots in your own projects'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgentSalesDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AgentSalesSerializer

    @extend_schema(
        responses={200: AgentSalesSerializer},
        description="Get a single agent sales record by ID. The record must belong to one of the user's projects.",
        summary="Get Agent Sale"
    )
    def get(self, request, sale_id):
        try:
            agent_sale = AgentSales.objects.select_related('plot', 'plot__project').get(
                id=sale_id,
                plot__project__user=request.user
            )
        except AgentSales.DoesNotExist:
            return Response(
                {'error': 'Agent sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AgentSalesSerializer(agent_sale)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=AgentSalesSerializer,
        responses={200: AgentSalesSerializer},
        description="Partially update an agent sales record. The record must belong to one of the user's projects.",
        summary="Update Agent Sale (Partial)"
    )
    def patch(self, request, sale_id):
        try:
            agent_sale = AgentSales.objects.get(id=sale_id, plot__project__user=request.user)
        except AgentSales.DoesNotExist:
            return Response(
                {'error': 'Agent sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AgentSalesSerializer(agent_sale, data=request.data, partial=True)
        if serializer.is_valid():
            # Validate plot change if provided
            plot = serializer.validated_data.get('plot')
            if plot and plot.project.user != request.user:
                return Response(
                    {'error': 'You can only assign plots from your own projects'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=AgentSalesSerializer,
        responses={200: AgentSalesSerializer},
        description="Fully update an agent sales record. The record must belong to one of the user's projects.",
        summary="Update Agent Sale (Full)"
    )
    def put(self, request, sale_id):
        try:
            agent_sale = AgentSales.objects.get(id=sale_id, plot__project__user=request.user)
        except AgentSales.DoesNotExist:
            return Response(
                {'error': 'Agent sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AgentSalesSerializer(agent_sale, data=request.data)
        if serializer.is_valid():
            # Validate plot
            plot = serializer.validated_data.get('plot')
            if plot and plot.project.user != request.user:
                return Response(
                    {'error': 'You can only assign plots from your own projects'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={204: None},
        description="Delete an agent sales record. The record must belong to one of the user's projects.",
        summary="Delete Agent Sale"
    )
    def delete(self, request, sale_id):
        try:
            agent_sale = AgentSales.objects.get(id=sale_id, plot__project__user=request.user)
        except AgentSales.DoesNotExist:
            return Response(
                {'error': 'Agent sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        agent_sale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
