from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from .models import PasswordReset


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
