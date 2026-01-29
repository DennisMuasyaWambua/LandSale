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
    phase = serializers.SerializerMethodField()

    class Meta:
        model = Plots
        fields = ['id', 'project', 'plot_number', 'phase', 'size', 'price', 'property_type', 'is_available', 'created_at', 'updated_at']

    def get_phase(self, obj):
        return self.context.get('booking_phase', '')


class BookingSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    plot_details = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        exclude = ['phase']

    def get_plot_details(self, instance):
        context = {'booking_phase': instance.phase}
        serializer = PlotDetailSerializer(instance.plot, context=context)
        return serializer.data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['balance'] = instance.purchase_price - instance.amount_paid
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

        # Validate phase against project's phases
        if phase:
            project_phases = plot.project.phase
            if not project_phases:
                raise serializers.ValidationError({
                    "phase": f"The project has no phases defined. Available phases: []"
                })
            if phase not in project_phases:
                raise serializers.ValidationError({
                    "phase": f"Phase '{phase}' is not available for this project. Available phases: {', '.join(project_phases)}"
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

        # Validate phase against project's phases
        if phase:
            project_phases = plot.project.phase
            if not project_phases:
                raise serializers.ValidationError({
                    "phase": f"The project has no phases defined. Available phases: []"
                })
            if phase not in project_phases:
                raise serializers.ValidationError({
                    "phase": f"Phase '{phase}' is not available for this project. Available phases: {', '.join(project_phases)}"
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