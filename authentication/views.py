from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample
import requests
import hashlib
import uuid
from .serializers import (UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
                         ForgotPasswordSerializer, ResetPasswordSerializer, SubscriptionPlanSerializer,
                         UserSubscriptionSerializer, PaymentSerializer, SubscribeSerializer)
from .models import PasswordReset, SubscriptionPlan, UserSubscription, Payment


@extend_schema(
    request=UserRegistrationSerializer,
    responses={201: UserSerializer},
    description="Register a new user account",
    examples=[
        OpenApiExample(
            "User Registration Example",
            value={
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "secure_password123",
                "password_confirm": "secure_password123"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=UserLoginSerializer,
    responses={200: UserSerializer},
    description="Login user and get JWT tokens",
    examples=[
        OpenApiExample(
            "User Login Example",
            value={
                "username": "john_doe",
                "password": "secure_password123"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    responses={200: UserSerializer},
    description="Get current user profile information"
)
@api_view(['GET'])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=ForgotPasswordSerializer,
    responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    description="Send password reset email to user",
    examples=[
        OpenApiExample(
            "Forgot Password Example",
            value={
                "email": "john@example.com"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Create password reset token
        reset = PasswordReset.objects.create(user=user)
        
        # Send email (in production, you would send actual email)
        # For now, we'll return the token in the response for testing
        try:
            reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset.token}"
            
            send_mail(
                subject='Password Reset Request',
                message=f'Click the link below to reset your password:\n{reset_url}\n\nThis link will expire in 1 hour.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=[email],
                fail_silently=False,
            )
            message = "Password reset email sent successfully"
        except Exception as e:
            # If email fails, still return success for security (don't reveal email configuration issues)
            # But include token for testing purposes
            message = f"Password reset initiated. Reset token: {reset.token} (for testing - in production this would be emailed)"
        
        return Response({
            'message': message
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=ResetPasswordSerializer,
    responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    description="Reset user password using token",
    examples=[
        OpenApiExample(
            "Reset Password Example",
            value={
                "token": "123e4567-e89b-12d3-a456-426614174000",
                "password": "new_secure_password123",
                "password_confirm": "new_secure_password123"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        reset = serializer.validated_data['reset']
        password = serializer.validated_data['password']

        # Update user password
        user = reset.user
        user.set_password(password)
        user.save()

        # Mark reset as used
        reset.is_used = True
        reset.save()

        return Response({
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============ SUBSCRIPTION PLAN MANAGEMENT (ADMIN) ============

@extend_schema(
    request=SubscriptionPlanSerializer,
    responses={201: SubscriptionPlanSerializer},
    description="Create a new subscription plan (Admin only)"
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_subscription_plan(request):
    serializer = SubscriptionPlanSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    responses={200: SubscriptionPlanSerializer(many=True)},
    description="List all subscription plans (Admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_subscription_plans_admin(request):
    plans = SubscriptionPlan.objects.all()
    serializer = SubscriptionPlanSerializer(plans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=SubscriptionPlanSerializer,
    responses={200: SubscriptionPlanSerializer},
    description="Update a subscription plan (Admin only)"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def update_subscription_plan(request, plan_id):
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': 'Subscription plan not found'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = SubscriptionPlanSerializer(plan, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    responses={204: None},
    description="Delete a subscription plan (Admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_subscription_plan(request, plan_id):
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
        plan.delete()
        return Response({'message': 'Subscription plan deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': 'Subscription plan not found'}, status=status.HTTP_404_NOT_FOUND)


# ============ SUBSCRIPTION PLANS (USER) ============

@extend_schema(
    responses={200: SubscriptionPlanSerializer(many=True)},
    description="List all active subscription plans"
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_active_subscription_plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    serializer = SubscriptionPlanSerializer(plans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: SubscriptionPlanSerializer},
    description="Get details of a specific subscription plan"
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_subscription_plan(request, plan_id):
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        serializer = SubscriptionPlanSerializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': 'Subscription plan not found'}, status=status.HTTP_404_NOT_FOUND)


# ============ USER SUBSCRIPTION ============

@extend_schema(
    responses={200: UserSubscriptionSerializer},
    description="Get current user's subscription status"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_subscription(request):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        subscription.check_and_update_status()
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except UserSubscription.DoesNotExist:
        return Response({'error': 'No subscription found', 'has_subscription': False}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    request=SubscribeSerializer,
    responses={200: {"type": "object"}},
    description="Initialize subscription payment with Pesapal"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_subscription(request):
    serializer = SubscribeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    plan_id = serializer.validated_data['plan_id']

    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': 'Invalid subscription plan'}, status=status.HTTP_404_NOT_FOUND)

    # Get or create user subscription
    subscription, created = UserSubscription.objects.get_or_create(
        user=request.user,
        defaults={'plan': plan, 'status': 'pending'}
    )

    if not created:
        # Update existing subscription
        subscription.plan = plan
        subscription.status = 'pending'
        subscription.save()

    # Generate unique merchant reference
    merchant_reference = f"SUB-{request.user.id}-{uuid.uuid4().hex[:8]}"

    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        subscription=subscription,
        plan=plan,
        amount=plan.amount,
        payment_type='subscription',
        pesapal_merchant_reference=merchant_reference,
        pesapal_order_tracking_id='',  # Will be populated after API call
        currency=getattr(settings, 'PESAPAL_CURRENCY', 'KES'),
        is_recurring=True
    )

    # Initialize Pesapal payment
    from .pesapal_service import initialize_payment
    try:
        result = initialize_payment(request.user, plan, subscription, payment)

        # Update payment with order_tracking_id
        payment.pesapal_order_tracking_id = result['order_tracking_id']
        payment.save()

        return Response({
            'message': 'Payment initialized successfully',
            'data': {
                'payment_url': result['redirect_url'],
                'order_tracking_id': result['order_tracking_id'],
                'merchant_reference': merchant_reference,
                'amount': plan.amount,
                'currency': payment.currency,
                'plan': SubscriptionPlanSerializer(plan).data
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        payment.status = 'failed'
        payment.metadata = {'error': str(e)}
        payment.save()
        return Response({
            'error': 'Payment initialization failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    responses={200: {"type": "object"}},
    description="Verify payment status with Pesapal"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request, order_tracking_id):
    try:
        payment = Payment.objects.get(
            pesapal_order_tracking_id=order_tracking_id,
            user=request.user
        )
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

    if payment.status == 'successful':
        return Response({
            'message': 'Payment already verified',
            'payment': PaymentSerializer(payment).data
        }, status=status.HTTP_200_OK)

    # Verify with Pesapal
    from .pesapal_service import verify_payment as pesapal_verify
    try:
        transaction_data = pesapal_verify(order_tracking_id)

        if transaction_data['payment_status_description'] == 'Completed':
            # Update payment
            payment.status = 'successful'
            payment.pesapal_transaction_id = transaction_data.get('confirmation_code')
            payment.payment_method = transaction_data.get('payment_method')
            payment.metadata = transaction_data
            payment.save()

            # Activate subscription
            subscription = payment.subscription
            subscription.activate_subscription()

            # Mark recurring as active if configured
            if payment.is_recurring:
                subscription.recurring_payment_active = True
                subscription.save()

            return Response({
                'message': 'Payment verified successfully',
                'payment': PaymentSerializer(payment).data,
                'subscription': UserSubscriptionSerializer(subscription).data
            }, status=status.HTTP_200_OK)
        else:
            payment.status = 'failed'
            payment.metadata = transaction_data
            payment.save()
            return Response({
                'error': 'Payment verification failed',
                'details': transaction_data.get('payment_status_description')
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'error': 'Payment verification failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    responses={200: {"type": "object"}},
    description="Pesapal IPN webhook for payment notifications"
)
@api_view(['GET'])  # Pesapal uses GET for IPN
@permission_classes([AllowAny])
@csrf_exempt
def pesapal_webhook(request):
    """
    Pesapal IPN webhook handler
    Receives: ?OrderTrackingId=xxx&OrderMerchantReference=xxx
    """
    order_tracking_id = request.GET.get('OrderTrackingId')

    if not order_tracking_id:
        return Response({'error': 'Missing OrderTrackingId'}, status=status.HTTP_400_BAD_REQUEST)

    # Process IPN notification
    from .pesapal_service import process_ipn_notification
    try:
        result = process_ipn_notification(order_tracking_id)
        return Response({'status': 'success', 'message': result.get('message', 'Processed')}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: {"type": "object"}},
    description="Cancel current user's subscription"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        subscription.cancel_subscription()
        return Response({
            'message': 'Subscription cancelled successfully',
            'subscription': UserSubscriptionSerializer(subscription).data
        }, status=status.HTTP_200_OK)
    except UserSubscription.DoesNotExist:
        return Response({'error': 'No active subscription found'}, status=status.HTTP_404_NOT_FOUND)


# ============ PAYMENT HISTORY ============

@extend_schema(
    responses={200: PaymentSerializer(many=True)},
    description="Get current user's payment history"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_history(request):
    payments = Payment.objects.filter(user=request.user)
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
