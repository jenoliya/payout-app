from django.contrib import auth
from django.db.models import Q
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from datetime import datetime, timedelta
import random
import uuid
from oauth2_provider.models import Application, AccessToken, RefreshToken

# import models
from django.contrib.auth.models import User

# login
class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(min_length=3, max_length=250, write_only=True, required=True)
    password = serializers.CharField(min_length=6, max_length=64, write_only=True, required=True)

    def login(self, **kwargs):
        email = self.validated_data['email']
        password = self.validated_data['password']

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"message": ["No active account found with the given credentials."]})

        user = auth.authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError({"message": ["No active account found with the given credentials."]})
        
        return user