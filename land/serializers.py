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

class PlotDetailSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Plots
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()
    plot_details = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'

    def get_balance(self, obj):
        return obj.purchase_price - obj.amount_paid

    def get_plot_details(self, obj):
        return PlotDetailSerializer(obj.plot).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['plot_details'] = self.get_plot_details(instance)
        return representation

    def validate(self, attrs):
        plot = attrs.get('plot')
        if not plot:
            raise serializers.ValidationError({
                "plot": "Please select a valid plot from the available plots."
            })
        return attrs

    def validate_amount_paid(self, value):
        if value < 0:
            raise serializers.ValidationError("Amount paid cannot be negative.")
        return value

    def validate_purchase_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Purchase price must be greater than 0.")
        return value