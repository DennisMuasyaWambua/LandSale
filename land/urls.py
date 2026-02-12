from django.urls import path
from .views import ProjectView, ProjectDetailView, BookingView, BookingUpdateView, PlotsView
urlpatterns = [
    path('create_project/', ProjectView.as_view(), name='project-create'),
    path('project/<int:project_id>/', ProjectDetailView.as_view(), name='project-detail'),
    path('create_booking/', BookingView.as_view(), name='booking-create'),
    path('create_booking/<int:booking_id>/', BookingUpdateView.as_view(), name='booking-update'),
    path('plots/', PlotsView.as_view(), name='plots-list'),
]