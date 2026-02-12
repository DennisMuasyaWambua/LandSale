from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Plots, Project, Booking, ProjectSales, AgentSales

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['user']

    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError("Size must be greater than 0.")
        return value

    def validate_project_svg_map(self, value):
        """
        Validate base64 data URL string.
        Reject strings larger than ~7MB to prevent database bloat.
        """
        if value:
            # Check if it's a data URL
            if not value.startswith('data:'):
                raise serializers.ValidationError(
                    "Invalid format. Expected a base64 data URL (e.g., data:image/svg+xml;base64,...)"
                )

            # Size limit: ~7MB base64 string (~5MB original file)
            MAX_SIZE = 7 * 1024 * 1024  # 7MB in bytes
            size = len(value.encode('utf-8'))

            if size > MAX_SIZE:
                size_mb = size / (1024 * 1024)
                raise serializers.ValidationError(
                    f"Base64 string too large ({size_mb:.2f}MB). Maximum allowed is 7MB (~5MB file)."
                )

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

    @extend_schema_field(serializers.CharField(max_length=100, help_text="Phase information from the booking"))
    def get_phase(self, obj):
        return self.context.get('booking_phase', '')


class BookingSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    plot_details = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        exclude = ['phase']

    @extend_schema_field(PlotDetailSerializer)
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

        # Only validate plot if it's being set (for create or update)
        # For partial updates (PATCH), plot might not be in attrs
        if 'plot' in attrs and not plot:
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
    plot_details = serializers.SerializerMethodField()
    phase = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = ProjectSales
        fields = '__all__'

    @extend_schema_field(PlotDetailSerializer)
    def get_plot_details(self, instance):
        context = {'booking_phase': instance.phase}
        serializer = PlotDetailSerializer(instance.plot, context=context)
        return serializer.data

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
    plot_details = serializers.SerializerMethodField()
    sub_agent_fee = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = AgentSales
        exclude = ['phase']

    @extend_schema_field(PlotDetailSerializer)
    def get_plot_details(self, instance):
        context = {'booking_phase': instance.phase}
        serializer = PlotDetailSerializer(instance.plot, context=context)
        return serializer.data

    def to_representation(self, instance):
        from decimal import Decimal
        representation = super().to_representation(instance)
        # Calculate sub_agent_fee: commission (percent) * purchase_price / 100
        # Use Decimal to avoid float/Decimal type mismatch
        representation['sub_agent_fee'] = (instance.commission * instance.purchase_price) / Decimal('100')
        return representation

    def validate(self, attrs):
        plot = attrs.get('plot')

        if not plot:
            raise serializers.ValidationError({
                "plot": "Please select a valid plot from the available plots."
            })

        # Auto-populate phase from plot if creating
        if not self.instance:  # Creating new record
            if plot.phase:
                attrs['phase'] = plot.phase[0] if isinstance(plot.phase, list) and len(plot.phase) > 0 else ''
            else:
                attrs['phase'] = ''

        return attrs

    def validate_commission(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Commission must be between 0 and 100 percent.")
        return value

    def validate_purchase_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Purchase price must be greater than 0.")
        return value


class PayInstallmentSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    agent_name = serializers.CharField(max_length=200)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    def validate_booking_id(self, value):
        if not Booking.objects.filter(id=value).exists():
            raise serializers.ValidationError("Booking not found.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class AgentSalesUpdateSerializer(serializers.ModelSerializer):
    """
    Restricted serializer for updating Agent Sales.
    Only allows updating: sub_agent_name, principal_agent, and commission.
    """
    class Meta:
        model = AgentSales
        fields = ['sub_agent_name', 'principal_agent', 'commission']

    def validate_commission(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Commission must be between 0 and 100 percent.")
        return value