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
from django.db import models
from drf_spectacular.utils import extend_schema, OpenApiExample
import requests
import hashlib
import uuid
from .serializers import (UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
                         ForgotPasswordSerializer, ResetPasswordSerializer, SubscriptionPlanSerializer,
                         UserSubscriptionSerializer, PaymentSerializer, SubscribeSerializer, SendEmailSerializer)
from .models import PasswordReset, SubscriptionPlan, UserSubscription, Payment


@extend_schema(
    request=UserRegistrationSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "User created successfully"},
                "user": {
                    "type": "object",
                    "description": "User details including role",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "is_active": {"type": "boolean"},
                        "date_joined": {"type": "string", "format": "date-time"},
                        "role": {"type": "string", "enum": ["admin", "staff", "user"], "description": "User role based on permissions"}
                    }
                },
                "access": {"type": "string", "description": "JWT access token"},
                "refresh": {"type": "string", "description": "JWT refresh token"}
            }
        }
    },
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
    responses={
        200: {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "Login successful"},
                "user": {
                    "type": "object",
                    "description": "User details including role",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "is_active": {"type": "boolean"},
                        "date_joined": {"type": "string", "format": "date-time"},
                        "role": {"type": "string", "enum": ["admin", "staff", "user"], "description": "User role based on permissions"}
                    }
                },
                "access": {"type": "string", "description": "JWT access token"},
                "refresh": {"type": "string", "description": "JWT refresh token"}
            }
        }
    },
    description="Login user with email and get JWT tokens with role information",
    examples=[
        OpenApiExample(
            "User Login Example",
            value={
                "email": "john@example.com",
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

        # For security, always return success message even if email doesn't exist
        try:
            user = User.objects.get(email=email)

            # Only send email if user exists and is active
            if user.is_active:
                # Create password reset token
                reset = PasswordReset.objects.create(user=user)

                # Send email
                try:
                    reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset.token}"

                    send_mail(
                        subject='Password Reset Request',
                        message=f'Click the link below to reset your password:\n{reset_url}\n\nThis link will expire in 1 hour.',
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                        recipient_list=[email],
                        fail_silently=False,
                    )
                except Exception as e:
                    # Log the error but don't expose it to the user
                    print(f"Email sending failed: {str(e)}")
                    # In development, you can uncomment below to get the token
                    # print(f"Reset token for {email}: {reset.token}")

        except User.DoesNotExist:
            # Don't reveal that user doesn't exist - just silently continue
            pass

        # Always return success message for security
        return Response({
            'message': 'If an account exists with this email, you will receive a password reset link shortly.'
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

        # Clean up old expired/used reset tokens for this user (housekeeping)
        from django.utils import timezone
        PasswordReset.objects.filter(
            user=user
        ).filter(
            models.Q(is_used=True) | models.Q(expires_at__lt=timezone.now())
        ).delete()

        return Response({
            'message': 'Password reset successfully. You can now login with your new password.'
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

        payment_status = transaction_data.get('payment_status_description', '').lower()

        if payment_status == 'completed':
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
    import logging
    logger = logging.getLogger('pesapal')

    order_tracking_id = request.GET.get('OrderTrackingId')
    merchant_reference = request.GET.get('OrderMerchantReference')

    logger.info(f"IPN received - OrderTrackingId: {order_tracking_id}, MerchantReference: {merchant_reference}")

    if not order_tracking_id:
        logger.error("IPN missing OrderTrackingId")
        return Response({'error': 'Missing OrderTrackingId'}, status=status.HTTP_400_BAD_REQUEST)

    # Process IPN notification
    from .pesapal_service import process_ipn_notification
    try:
        result = process_ipn_notification(order_tracking_id)
        logger.info(f"IPN processed successfully for {order_tracking_id}: {result}")
        return Response({'status': 'success', 'message': result.get('message', 'Processed')}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"IPN processing error for {order_tracking_id}: {str(e)}", exc_info=True)
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

    # Auto-verify pending payments to ensure status is up-to-date
    from .pesapal_service import verify_payment as pesapal_verify
    from django.utils import timezone
    from datetime import timedelta

    for payment in payments:
        # Only verify pending payments that have an order_tracking_id and are less than 24 hours old
        if (payment.status == 'pending' and
            payment.pesapal_order_tracking_id and
            payment.created_at > timezone.now() - timedelta(hours=24)):
            try:
                transaction_data = pesapal_verify(payment.pesapal_order_tracking_id)

                payment_status = transaction_data.get('payment_status_description', '').lower()

                if payment_status == 'completed':
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

                elif payment_status == 'failed':
                    payment.status = 'failed'
                    payment.metadata = transaction_data
                    payment.save()
            except Exception as e:
                # Log error but continue to return payment history
                print(f"Error auto-verifying payment {payment.id}: {str(e)}")
                pass

    # Refresh payments from database to get updated status
    payments = Payment.objects.filter(user=request.user)
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ============ ADMIN USER CREATION ============

@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'description': 'Username for the admin user'},
                'email': {'type': 'string', 'format': 'email', 'description': 'Email address'},
                'password': {'type': 'string', 'description': 'Password for the admin user'},
                'first_name': {'type': 'string', 'description': 'First name (optional)'},
                'last_name': {'type': 'string', 'description': 'Last name (optional)'},
            },
            'required': ['username', 'email', 'password']
        }
    },
    responses={
        201: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'user': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'username': {'type': 'string'},
                        'email': {'type': 'string'},
                        'is_staff': {'type': 'boolean'},
                        'is_superuser': {'type': 'boolean'},
                    }
                }
            }
        }
    },
    description="Create a new admin user (superuser). Only accessible by existing superusers.",
    summary="Create Admin User"
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_admin_user(request):
    """
    Create a new admin user with staff and superuser privileges.
    Only accessible by existing superusers.
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    # Validation
    if not username or not email or not password:
        return Response({
            'error': 'Missing required fields',
            'required': ['username', 'email', 'password']
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'Username already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({
            'error': 'Email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Create admin user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        return Response({
            'message': 'Admin user created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Failed to create admin user',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============ EMAIL SENDING ============

@extend_schema(
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'subject': {
                    'type': 'string',
                    'description': 'Email subject line',
                    'example': 'Important Update'
                },
                'body': {
                    'type': 'string',
                    'description': 'Email body content (can be HTML or plain text)',
                    'example': 'Dear valued customer, this is an important update...'
                },
                'to': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'email'},
                    'description': 'List of recipient email addresses',
                    'example': ['user1@example.com', 'user2@example.com']
                },
                'cc': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'email'},
                    'description': 'List of CC email addresses (optional)',
                    'example': ['manager@example.com']
                },
                'bcc': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'email'},
                    'description': 'List of BCC email addresses (optional)',
                    'example': ['archive@example.com']
                },
                'attachments': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'binary'},
                    'description': 'File attachments (optional, multiple files supported)'
                }
            },
            'required': ['subject', 'body', 'to']
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'recipients': {
                    'type': 'object',
                    'properties': {
                        'to': {'type': 'array', 'items': {'type': 'string'}},
                        'cc': {'type': 'array', 'items': {'type': 'string'}},
                        'bcc': {'type': 'array', 'items': {'type': 'string'}},
                        'total': {'type': 'integer'}
                    }
                },
                'attachments_count': {'type': 'integer'}
            }
        }
    },
    description="Send an email with optional CC, BCC, and file attachments. Supports multiple recipients and multiple file uploads.",
    summary="Send Email"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_email(request):
    """
    Send an email with optional CC, BCC, and file attachments.

    Supports:
    - Multiple recipients (to, cc, bcc)
    - Multiple file attachments
    - HTML or plain text email body
    - Maximum 100 total recipients
    - Maximum 10MB per attachment (configurable)
    """
    import json
    from django.core.mail import EmailMessage

    # Parse JSON fields from form data
    data = {}
    for key in ['subject', 'body', 'to', 'cc', 'bcc']:
        value = request.data.get(key)
        if value:
            # Handle array fields (to, cc, bcc)
            if key in ['to', 'cc', 'bcc']:
                if isinstance(value, str):
                    try:
                        data[key] = json.loads(value)
                    except json.JSONDecodeError:
                        # If it's a single email as string, convert to list
                        data[key] = [value]
                else:
                    data[key] = value
            else:
                data[key] = value

    # Validate the email data
    serializer = SendEmailSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data

    # Prepare email
    subject = validated_data['subject']
    body = validated_data['body']
    to_emails = validated_data['to']
    cc_emails = validated_data.get('cc', [])
    bcc_emails = validated_data.get('bcc', [])

    # Get FROM email from settings
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    # Create email message
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=to_emails,
            cc=cc_emails,
            bcc=bcc_emails,
        )

        # Detect if body contains HTML
        if '<html' in body.lower() or '<p>' in body.lower() or '<br' in body.lower():
            email.content_subtype = 'html'

        # Handle file attachments
        attachments_count = 0
        max_file_size = 10 * 1024 * 1024  # 10MB

        if request.FILES:
            for file_key in request.FILES:
                files = request.FILES.getlist(file_key)
                for uploaded_file in files:
                    # Check file size
                    if uploaded_file.size > max_file_size:
                        return Response({
                            'error': f'File "{uploaded_file.name}" exceeds maximum size of 10MB'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Attach file
                    email.attach(
                        uploaded_file.name,
                        uploaded_file.read(),
                        uploaded_file.content_type
                    )
                    attachments_count += 1

        # Send email
        email.send(fail_silently=False)

        return Response({
            'message': 'Email sent successfully',
            'recipients': {
                'to': to_emails,
                'cc': cc_emails,
                'bcc': bcc_emails,
                'total': len(to_emails) + len(cc_emails) + len(bcc_emails)
            },
            'attachments_count': attachments_count,
            'from': from_email
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to send email',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'password': {'type': 'string', 'minLength': 8},
                'phone_number': {'type': 'string'},
                'project_ids': {'type': 'array', 'items': {'type': 'integer'}},
            },
            'required': ['username', 'email', 'password', 'project_ids']
        }
    },
    responses={201: UserSerializer},
    description="Admin creates a subagent and assigns them to projects",
    summary="Create Subagent (Admin Only)"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subagent(request):
    """
    Create a subagent user and assign them to projects.
    Only admins can create subagents and assign them to their own projects.
    """
    # Check user is admin or super_admin
    if not hasattr(request.user, 'profile') or request.user.profile.user_type not in ['admin', 'super_admin']:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

    # Extract data
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    phone_number = request.data.get('phone_number', '')
    project_ids = request.data.get('project_ids', [])

    # Validate required fields
    if not username or not email or not password:
        return Response({
            'error': 'username, email, and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not project_ids:
        return Response({
            'error': 'At least one project must be assigned'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if username or email already exists
    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'Username already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({
            'error': 'Email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate admin owns these projects
    from land.models import Project, ProjectAssignment
    projects = Project.objects.filter(id__in=project_ids, user=request.user)
    if len(projects) != len(project_ids):
        return Response({
            'error': 'You can only assign subagents to your own projects'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create UserProfile
        from authentication.models import UserProfile
        UserProfile.objects.create(
            user=user,
            user_type='subagent',
            phone_number=phone_number,
            assigned_by=request.user
        )

        # Create project assignments
        for project in projects:
            ProjectAssignment.objects.create(
                user=user,
                project=project,
                assigned_by=request.user,
                assignment_type='book'
            )

        return Response({
            'message': 'Subagent created successfully',
            'user': UserSerializer(user).data,
            'assigned_projects': [{'id': p.id, 'name': p.name} for p in projects]
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Failed to create subagent',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
