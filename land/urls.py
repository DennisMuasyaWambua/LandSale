from django.urls import path
from .views import LandView
urlpatterns = [
    path('properties/', LandView.as_view(), name='land-create'),
]