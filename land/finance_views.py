from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from land.models import ProjectSales, AgentSales
from land.serializers import ProjectSalesSerializer, AgentSalesSerializer


class ProjectSalesListCreateView(APIView):
    serializer_class = ProjectSalesSerializer

    @extend_schema(
        responses={200: ProjectSalesSerializer(many=True)},
        description="Get all project sales records with plot and balance details",
        summary="List Project Sales"
    )
    def get(self, request):
        project_sales = ProjectSales.objects.select_related('plot', 'plot__project').all()
        serializer = ProjectSalesSerializer(project_sales, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ProjectSalesSerializer,
        responses={201: ProjectSalesSerializer},
        description="Create a new project sales record with client, plot, phase, purchase price, and deposit",
        summary="Create Project Sale"
    )
    def post(self, request):
        serializer = ProjectSalesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectSalesDetailView(APIView):
    serializer_class = ProjectSalesSerializer

    @extend_schema(
        responses={200: ProjectSalesSerializer},
        description="Get a single project sales record by ID with full details and balance calculation",
        summary="Get Project Sale"
    )
    def get(self, request, sale_id):
        try:
            project_sale = ProjectSales.objects.select_related('plot', 'plot__project').get(id=sale_id)
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
        description="Partially update a project sales record (only provided fields will be updated)",
        summary="Update Project Sale (Partial)"
    )
    def patch(self, request, sale_id):
        try:
            project_sale = ProjectSales.objects.get(id=sale_id)
        except ProjectSales.DoesNotExist:
            return Response(
                {'error': 'Project sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProjectSalesSerializer(project_sale, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=ProjectSalesSerializer,
        responses={200: ProjectSalesSerializer},
        description="Fully update a project sales record (all fields required)",
        summary="Update Project Sale (Full)"
    )
    def put(self, request, sale_id):
        try:
            project_sale = ProjectSales.objects.get(id=sale_id)
        except ProjectSales.DoesNotExist:
            return Response(
                {'error': 'Project sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProjectSalesSerializer(project_sale, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={204: None},
        description="Delete a project sales record by ID",
        summary="Delete Project Sale"
    )
    def delete(self, request, sale_id):
        try:
            project_sale = ProjectSales.objects.get(id=sale_id)
        except ProjectSales.DoesNotExist:
            return Response(
                {'error': 'Project sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        project_sale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentSalesListCreateView(APIView):
    serializer_class = AgentSalesSerializer

    @extend_schema(
        responses={200: AgentSalesSerializer(many=True)},
        description="Get all agent sales records with plot, commission, and agent details",
        summary="List Agent Sales"
    )
    def get(self, request):
        agent_sales = AgentSales.objects.select_related('plot', 'plot__project').all()
        serializer = AgentSalesSerializer(agent_sales, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=AgentSalesSerializer,
        responses={201: AgentSalesSerializer},
        description="Create a new agent sales record with plot, commission, and agent information",
        summary="Create Agent Sale"
    )
    def post(self, request):
        serializer = AgentSalesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgentSalesDetailView(APIView):
    serializer_class = AgentSalesSerializer

    @extend_schema(
        responses={200: AgentSalesSerializer},
        description="Get a single agent sales record by ID with full details",
        summary="Get Agent Sale"
    )
    def get(self, request, sale_id):
        try:
            agent_sale = AgentSales.objects.select_related('plot', 'plot__project').get(id=sale_id)
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
        description="Partially update an agent sales record (only provided fields will be updated)",
        summary="Update Agent Sale (Partial)"
    )
    def patch(self, request, sale_id):
        try:
            agent_sale = AgentSales.objects.get(id=sale_id)
        except AgentSales.DoesNotExist:
            return Response(
                {'error': 'Agent sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AgentSalesSerializer(agent_sale, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=AgentSalesSerializer,
        responses={200: AgentSalesSerializer},
        description="Fully update an agent sales record (all fields required)",
        summary="Update Agent Sale (Full)"
    )
    def put(self, request, sale_id):
        try:
            agent_sale = AgentSales.objects.get(id=sale_id)
        except AgentSales.DoesNotExist:
            return Response(
                {'error': 'Agent sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AgentSalesSerializer(agent_sale, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={204: None},
        description="Delete an agent sales record by ID",
        summary="Delete Agent Sale"
    )
    def delete(self, request, sale_id):
        try:
            agent_sale = AgentSales.objects.get(id=sale_id)
        except AgentSales.DoesNotExist:
            return Response(
                {'error': 'Agent sale not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        agent_sale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
