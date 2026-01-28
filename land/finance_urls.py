from django.urls import path
from .finance_views import (
    ProjectSalesListCreateView,
    ProjectSalesDetailView,
    AgentSalesListCreateView,
    AgentSalesDetailView
)

urlpatterns = [
    # Project Sales endpoints
    path('project-sales/', ProjectSalesListCreateView.as_view(), name='project-sales-list-create'),
    path('project-sales/<int:sale_id>/', ProjectSalesDetailView.as_view(), name='project-sales-detail'),

    # Agent Sales endpoints
    path('agent-sales/', AgentSalesListCreateView.as_view(), name='agent-sales-list-create'),
    path('agent-sales/<int:sale_id>/', AgentSalesDetailView.as_view(), name='agent-sales-detail'),
]
