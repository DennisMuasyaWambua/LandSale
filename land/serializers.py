from rest_framework import serializers
from .models import Plots, Project, Booking, ProjectSales, AgentSales

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
    
    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError("Size must be greater than 0.")
        return value

class PlotsSerializer(serializers.ModelSerializer):
    phase = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Plots
        fields = '__all__'
        read_only_fields = ['is_available']

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

    def create(self, validated_data):
        phase = validated_data.pop('phase', '')
        if phase:
            validated_data['phase'] = [phase]
        else:
            validated_data['phase'] = []
        return super().create(validated_data)

class PlotDetailSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Plots
        exclude = ['phase']


class BookingSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    plot_details = PlotDetailSerializer(source='plot', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['balance'] = instance.purchase_price - instance.amount_paid

        # Move phase inside plot_details, positioned after price
        if 'plot_details' in representation and 'phase' in representation:
            phase_value = representation.pop('phase')
            plot_details = representation['plot_details']

            # Reconstruct plot_details with phase after price
            ordered_plot_details = {}
            for key, value in plot_details.items():
                ordered_plot_details[key] = value
                if key == 'price':
                    ordered_plot_details['phase'] = phase_value

            representation['plot_details'] = ordered_plot_details

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


class ProjectSalesSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    plot_details = PlotDetailSerializer(source='plot', read_only=True)

    class Meta:
        model = ProjectSales
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['balance'] = instance.purchase_price - instance.deposit
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

    def validate_deposit(self, value):
        if value < 0:
            raise serializers.ValidationError("Deposit cannot be negative.")
        return value

    def validate_purchase_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Purchase price must be greater than 0.")
        return value


class AgentSalesSerializer(serializers.ModelSerializer):
    plot_details = PlotDetailSerializer(source='plot', read_only=True)
    sub_agent_fee = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = AgentSales
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Calculate sub_agent_fee: commission (percent) * purchase_price / 100
        representation['sub_agent_fee'] = (instance.commission * instance.purchase_price) / 100
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

    def validate_commission(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Commission must be between 0 and 100 percent.")
        return value

    def validate_purchase_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Purchase price must be greater than 0.")
        return value