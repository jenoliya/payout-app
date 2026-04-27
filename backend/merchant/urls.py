from django.urls import path

# views
from . import views

urlpatterns = [
    path('create/', views.MerchantView.as_view(), name='create-merchant'),
]