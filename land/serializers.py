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
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    plot_details = PlotDetailSerializer(source='plot', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['balance'] = instance.purchase_price - instance.amount_paid
        return representation

    def validate(self, attrs):
        plot = attrs.get('plot')
        phase = attrs.get('phase')

        if not plot:
            raise serializers.ValidationError({
                "plot": "Please select a valid plot from the available plots."
            })

        # Validate phase if provided
        if phase:
            if not plot.phase:
                raise serializers.ValidationError({
                    "phase": f"The selected plot has no phases defined. Available phases: []"
                })
            if phase not in plot.phase:
                raise serializers.ValidationError({
                    "phase": f"Phase '{phase}' is not available for this plot. Available phases: {', '.join(plot.phase)}"
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