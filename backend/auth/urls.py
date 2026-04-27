from django.urls import include, path
from oauth2_provider import urls as oauth2_urls

from . import views

urlpatterns = [
    # path('/', include(oauth2_urls)),
    path('login/', views.LoginView.as_view(), name='login'), # [POST] login
]