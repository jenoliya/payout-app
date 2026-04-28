from rest_framework import serializers
from uuid import uuid4

# models
from django.contrib.auth.models import User
from payout.models import Merchant

# create merchant
class CreateMerchantSerializer(serializers.Serializer):
    email = serializers.CharField(min_length=3, max_length=250, write_only=True, required=True)
    password = serializers.CharField(min_length=6, max_length=64, write_only=True, required=True)
    first_name = serializers.CharField(min_length=3, max_length=250, required=True)
    last_name = serializers.CharField(min_length=3, max_length=250, required=True)
    def create(self):
        
        email = self.validated_data['email']
        password = self.validated_data['password']

        user = User.objects.filter(email=email).first()
        if user:
            raise serializers.ValidationError({"message": ["Merchant account already exists with the given email address"]})
        
        user = User.objects.create_user(
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            username=uuid4(),
            email=email,
            password=password
        )

        merchant = Merchant.objects.create(
            name = self.validated_data['first_name']+" "+self.validated_data['last_name'],
            avaliable_balance_in_paise = 0,
            user = user
        )

        return merchant