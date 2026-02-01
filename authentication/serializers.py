from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import PasswordReset, SubscriptionPlan, UserSubscription, Payment


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'role']
        read_only_fields = ['id', 'date_joined', 'role']

    def get_role(self, obj):
        if obj.is_superuser:
            return 'admin'
        elif obj.is_staff:
            return 'staff'
        else:
            return 'user'


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            
            raise serializers.ValidationError("Password fields didn't match.")

        try:
            reset = PasswordReset.objects.get(token=attrs['token'])
            if not reset.is_valid():
                raise serializers.ValidationError("Reset token has expired or been used")
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
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan")
        return value