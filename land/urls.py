from django.urls import path
from .views import ProjectView, ProjectDetailView, BookingView, PlotsView, ProjectMapImageView
urlpatterns = [
    path('create_project/', ProjectView.as_view(), name='project-create'),
    path('project/<int:project_id>/', ProjectDetailView.as_view(), name='project-detail'),
    path('project/<int:project_id>/map/', ProjectMapImageView.as_view(), name='project-map-image'),
    path('create_booking/', BookingView.as_view(), name='booking-create'),
    path('plots/', PlotsView.as_view(), name='plots-list'),
]