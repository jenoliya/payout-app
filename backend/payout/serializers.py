from rest_framework import serializers

# models
from .models import Payout

# create payout request
class PayoutRequestSerializer(serializers.Serializer):
    email = serializers.CharField(min_length=3, max_length=250, write_only=True, required=True),
    amount_in_paise = serializers.IntegerField(required=True)
    idempotency_key = serializers.CharField(required=True)