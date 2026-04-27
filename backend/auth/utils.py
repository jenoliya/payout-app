from django.utils import timezone
from django.conf import settings
from oauthlib.common import generate_token
from datetime import datetime, timedelta
import random
import uuid
import requests

# import exceptions
from auth.exceptions import AuthException

# import models
from django.contrib.auth.models import User
from oauth2_provider.models import Application, AccessToken, RefreshToken


class AuthUtils:

    @staticmethod
    def create_user(first_name, email, password, login_provider):
        # check user exist by email
        user = User.objects.filter(email=email)
        if User.objects.filter(email=email).exists():
            return user.first()
        
        # create user
        username = uuid.uuid4()
        user = User.objects.create_user(
            first_name=first_name,
            username=username,
            email=email,
            password=password
        )

        return user

    # generate OAuth JWT token
    @staticmethod
    def generate_oauth_token(user):
        application = Application.objects.get(client_id = settings.OAUTH2_CLIENT_ID)
        expires = timezone.now() + timezone.timedelta(settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'])
        access_token = AccessToken(user=user, scope='read write groups', expires=expires,token=generate_token(),application=application )
        access_token.save()
        refresh_token = RefreshToken(user=user, token=generate_token(), application=application, access_token=access_token)
        refresh_token.save()

        # generate JSON output
        token = {
            "access_token_life_time_in_seconds": settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'],
            "refresh_token_life_time_in_seconds": settings.OAUTH2_PROVIDER['REFRESH_TOKEN_EXPIRE_SECONDS'],
            "access_token": str(access_token),
            "refresh_token": str(refresh_token),
        }
        return token     