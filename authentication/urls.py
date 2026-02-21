from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),

    # Admin subscription plan management
    path('admin/subscription-plans/', views.create_subscription_plan, name='create_subscription_plan'),
    path('admin/subscription-plans/list/', views.list_subscription_plans_admin, name='list_subscription_plans_admin'),
    path('admin/subscription-plans/<int:plan_id>/', views.update_subscription_plan, name='update_subscription_plan'),
    path('admin/subscription-plans/<int:plan_id>/delete/', views.delete_subscription_plan, name='delete_subscription_plan'),

    # Admin user management
    path('admin/create-admin/', views.create_admin_user, name='create_admin_user'),
    path('admin/create-subagent/', views.create_subagent, name='create_subagent'),

    # User subscription endpoints
    path('subscription-plans/', views.list_active_subscription_plans, name='list_active_subscription_plans'),
    path('subscription-plans/<int:plan_id>/', views.get_subscription_plan, name='get_subscription_plan'),
    path('my-subscription/', views.get_my_subscription, name='get_my_subscription'),
    path('subscribe/', views.initialize_subscription, name='initialize_subscription'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),

    # Payment endpoints
    path('payment/verify/<str:order_tracking_id>/', views.verify_payment, name='verify_payment'),
    path('payment/history/', views.get_payment_history, name='get_payment_history'),
    path('webhook/pesapal/', views.pesapal_webhook, name='pesapal_webhook'),

    # Email endpoint
    path('send-email/', views.send_email, name='send_email'),
]