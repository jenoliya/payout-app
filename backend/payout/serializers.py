from rest_framework import serializers

# create payout request
class PayoutRequestSerializer(serializers.Serializer):
    email = serializers.CharField(min_length=3, max_length=250, write_only=True, required=True),
    amount_in_paise = serializers.IntegerField(required=True)
    idempotency_key = serializers.CharField(required=True)

# payout serializer
class PayoutSerilaizer(serializers.Serializer):
    amount_in_paise = serializers.IntegerField(required=True)
    status = serializers.CharField(required=True)
    created_at = serializers.DateTimeField(read_only=True)

# ledger serializer
class LedgerSerializer(serializers.Serializer):
    amount_in_paise = serializers.IntegerField(required=True)
    entry_type = serializers.CharField(required=True)
    created_at = serializers.DateTimeField(read_only=True)