"""
Subscription Enforcement Middleware
Ensures users have active subscriptions to access protected endpoints
"""

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import UserSubscription


class SubscriptionRequiredMiddleware(MiddlewareMixin):
    """
    Middleware to enforce subscription requirement on protected endpoints
    """

    EXEMPT_PATHS = [
        '/auth/register/',
        '/auth/login/',
        '/auth/profile/',
        '/auth/refresh/',
        '/auth/forgot-password/',
        '/auth/reset-password/',
        '/auth/subscription-plans/',
        '/auth/subscribe/',
        '/auth/payment/verify/',
        '/auth/webhook/',
        '/admin/',
        '/api/docs/',
        '/api/schema/',
    ]

    def process_request(self, request):
        """
        Check if user has active subscription before allowing access
        """
        # Check if path is exempt
        path = request.path
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return None

        # Try to authenticate user from JWT token
        jwt_auth = JWTAuthentication()
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result is not None:
                user, token = auth_result
                request.user = user
            else:
                # No authentication provided, let the view handle it
                return None
        except AuthenticationFailed:
            # Invalid token, let the view handle it
            return None
        except Exception:
            # Other authentication errors, let the view handle it
            return None

        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return None  # Let authentication handler deal with it

        # Admins bypass subscription check
        if request.user.is_staff or request.user.is_superuser:
            return None

        # Check subscription
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            subscription.check_and_update_status()

            if not subscription.is_active():
                return JsonResponse({
                    'error': 'Active subscription required',
                    'message': 'Your subscription has expired. Please renew to continue.',
                    'subscription_status': subscription.status,
                    'has_active_subscription': False
                }, status=403)
        except UserSubscription.DoesNotExist:
            return JsonResponse({
                'error': 'Subscription required',
                'message': 'Please subscribe to a plan to access this service.',
                'has_subscription': False,
                'has_active_subscription': False
            }, status=403)

        return None
