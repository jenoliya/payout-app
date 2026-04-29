from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('setup/', views.CreateOAuthAppView.as_view(), name='create-oauth-app'),
]