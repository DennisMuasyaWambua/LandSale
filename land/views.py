from django.shortcuts import render
from rest_framework.views import APIView 
from rest_framework.response import  Response

from land.models import Land
from land.serializers import LandSerializer
# Create your views here.
class LandView(APIView):
    def post(self, request):
        data = request.data
        serializer = LandSerializer(data=data)
        if serializer.is_valid():
            
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    def get(self, request):
        lands = Land.objects.all()
        serializer = LandSerializer(lands, many=True)
        return Response(serializer.data, status=200)