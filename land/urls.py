from django.urls import path
from .views import ProjectView, BookingView, PlotsView
urlpatterns = [
    path('create_project/', ProjectView.as_view(), name='project-create'),
    path('create_booking/', BookingView.as_view(), name='booking-create'),
    path('plots/', PlotsView.as_view(), name='plots-list'),
]