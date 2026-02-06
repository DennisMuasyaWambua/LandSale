from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('projects/', views.DashboardProjectsView.as_view(), name='dashboard-projects'),
    path('bookings/', views.DashboardBookingsView.as_view(), name='dashboard-bookings'),
    path('bookings/<int:booking_id>/', views.DashboardUpdateBookingView.as_view(), name='dashboard-update-booking'),
    path('recent-activity/', views.DashboardRecentActivityView.as_view(), name='dashboard-recent-activity'),
    path('payinstallment/', views.PayInstallmentView.as_view(), name='pay-installment'),
]