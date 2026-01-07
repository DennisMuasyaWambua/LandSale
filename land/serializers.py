from rest_framework import serializers
from .models import Plots, Project, Booking

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
    
    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError("Size must be greater than 0.")
        return value

class PlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plots
        fields = '__all__'
    
    def validate(self, attrs):
        project = attrs.get('project')
        if not project:
            raise serializers.ValidationError({
                "project": "Please select a valid project. Create a project first if none exist."
            })
        return attrs
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
    
    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError("Size must be greater than 0.")
        return value

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
    
    def validate(self, attrs):
        plot = attrs.get('plot')
        if not plot:
            raise serializers.ValidationError({
                "plot": "Please select a valid plot from the available plots."
            })
        return attrs
    
    def validate_amount_paid(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount paid must be greater than 0.")
        return value