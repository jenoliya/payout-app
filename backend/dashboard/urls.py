from django.urls import path

# views
from .import views

urlpatterns = [
    # get dashboard
    path('', views.GetDashboardView.as_view(), name='get-dashboard'),
]