from rest_framework.permissions import BasePermission
from .models import UserSubscription


class HasActiveSubscription(BasePermission):
    message = "You must have an active subscription to access this resource."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            subscription = UserSubscription.objects.get(user=request.user)
            subscription.check_and_update_status()
            return subscription.is_active()
        except UserSubscription.DoesNotExist:
            return False


class IsSubscribedOrAdmin(BasePermission):
    message = "You must have an active subscription or be an admin to access this resource."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_staff or request.user.is_superuser:
            return True

        try:
            subscription = UserSubscription.objects.get(user=request.user)
            subscription.check_and_update_status()
            return subscription.is_active()
        except UserSubscription.DoesNotExist:
            return False
