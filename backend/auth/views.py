from django.shortcuts import render

# Create your views here.
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from oauthlib.common import generate_token
import jwt
import hashlib

# import exceptions
from .exceptions import AuthException

# import models
from django.contrib.auth.models import User
from oauth2_provider.models import Application, AccessToken, RefreshToken

from .serializers import LoginSerializer

from .utils import AuthUtils

class LoginView(APIView):
    permission_classes = (AllowAny, )
    login_serializer_class = LoginSerializer

    def post(self, request):
        try:
            # validate user input
            serializer = self.login_serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            # login
            user = serializer.login()

            # generate JWT token
            token = AuthUtils.generate_oauth_token(user)

            # generate JSON output
            output = {
                # user information
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,

               
                # token
                "access_token_life_time_in_seconds": settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'],
                "refresh_token_life_time_in_seconds": settings.OAUTH2_PROVIDER['REFRESH_TOKEN_EXPIRE_SECONDS'],
                "access_token": str(token.get("access_token")),
                "refresh_token": str(token.get("refresh_token")),
            }   

            return Response(output, status=status.HTTP_200_OK)
        except Application.DoesNotExist:
            return Response({"message": "OAuth application does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        except AuthException as e:
            return Response({"message": e.message}, status=status.HTTP_400_BAD_REQUEST)

class CreateOAuthAppView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        client_id = settings.OAUTH2_CLIENT_ID
        client_secret = settings.OAUTH2_CLIENT_SECRET

        if not client_id or not client_secret:
            return Response(
                {"message": "OAUTH2_CLIENT_ID and OAUTH2_CLIENT_SECRET must be set in environment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if Application.objects.filter(client_id=client_id).exists():
            return Response(
                {"message": "OAuth application already exists."},
                status=status.HTTP_200_OK,
            )

        Application.objects.create(
            name="PayApp",
            client_id=client_id,
            client_secret=client_secret,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_PASSWORD,
        )

        return Response({"message": "OAuth application created."}, status=status.HTTP_201_CREATED)