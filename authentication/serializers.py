from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import PasswordReset, SubscriptionPlan, UserSubscription, Payment


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'phone_number']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        phone_number = validated_data.pop('phone_number', '')

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create UserProfile with user_type='client' (default for self-registration)
        from authentication.models import UserProfile
        UserProfile.objects.create(
            user=user,
            user_type='client',
            phone_number=phone_number
        )

        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                user = authenticate(username=user.username, password=password)
                if not user:
                    raise serializers.ValidationError('Invalid credentials')
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled')
                attrs['user'] = user
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials')
        else:
            raise serializers.ValidationError('Must include email and password')

        return attrs


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'role', 'user_type', 'phone_number']
        read_only_fields = ['id', 'date_joined', 'role', 'user_type', 'phone_number']

    def get_role(self, obj):
        # Legacy role field - kept for backwards compatibility
        if obj.is_superuser:
            return 'admin'
        elif obj.is_staff:
            return 'staff'
        else:
            return 'user'

    def get_user_type(self, obj):
        # New user_type field from UserProfile
        if hasattr(obj, 'profile'):
            return obj.profile.user_type
        return None

    def get_phone_number(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.phone_number
        return None


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # For security, don't reveal if email exists or not
        # Just validate email format (done by EmailField)
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate_token(self, value):
        """Validate that the token exists and is valid"""
        try:
            reset = PasswordReset.objects.get(token=value)
            if reset.is_used:
                raise serializers.ValidationError("This reset link has already been used. Please request a new password reset.")
            if not reset.is_valid():
                raise serializers.ValidationError("This reset link has expired. Please request a new password reset.")
            return value
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token. Please request a new password reset.")

    def validate(self, attrs):
        # Check password match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Password fields didn't match."})

        # Get the reset object (we already validated it exists in validate_token)
        try:
            reset = PasswordReset.objects.get(token=attrs['token'])
            attrs['reset'] = reset
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token")

        return attrs


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    duration_in_days = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'description', 'amount', 'period', 'period_count',
                  'is_active', 'features', 'duration_in_days', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_duration_in_days(self, obj):
        return obj.get_duration_in_days()


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    is_currently_active = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'user_details', 'plan', 'plan_details', 'status',
                  'start_date', 'end_date', 'auto_renew', 'recurring_payment_active',
                  'last_recurring_payment_date', 'is_currently_active',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'status', 'start_date', 'end_date',
                           'recurring_payment_active', 'last_recurring_payment_date',
                           'created_at', 'updated_at']

    def get_is_currently_active(self, obj):
        return obj.is_active()


class PaymentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'user', 'user_details', 'subscription', 'plan', 'plan_details',
                  'amount', 'payment_type', 'status', 'pesapal_order_tracking_id',
                  'pesapal_merchant_reference', 'pesapal_transaction_id',
                  'payment_method', 'currency', 'is_recurring', 'recurring_frequency',
                  'metadata', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'status', 'pesapal_transaction_id',
                           'payment_method', 'created_at', 'updated_at']


class SubscribeSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()

    def validate_plan_id(self, value):
        if not SubscriptionPlan.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive subscription plan")
        return value


class SendEmailSerializer(serializers.Serializer):
    """
    Serializer for sending emails with attachments
    """
    subject = serializers.CharField(max_length=255, required=True)
    body = serializers.CharField(required=True, allow_blank=False)
    to = serializers.ListField(
        child=serializers.EmailField(),
        required=True,
        allow_empty=False,
        help_text="List of recipient email addresses"
    )
    cc = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True,
        help_text="List of CC email addresses"
    )
    bcc = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True,
        help_text="List of BCC email addresses"
    )
    # File attachments will be handled separately via request.FILES

    def validate_to(self, value):
        """Validate that at least one recipient is provided"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one recipient email is required")
        return value

    def validate(self, attrs):
        """Additional validation for email data"""
        # Ensure total recipients don't exceed reasonable limit
        total_recipients = len(attrs.get('to', []))
        total_recipients += len(attrs.get('cc', []))
        total_recipients += len(attrs.get('bcc', []))

        if total_recipients > 100:
            raise serializers.ValidationError(
                "Total number of recipients (to + cc + bcc) cannot exceed 100"
            )

        return attrs