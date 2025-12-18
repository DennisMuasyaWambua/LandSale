from rest_framework import serializers
from .models import Plots, Project, Booking

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
class PlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plots
        fields = '__all__'
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'