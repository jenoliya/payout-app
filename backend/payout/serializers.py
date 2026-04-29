from rest_framework import serializers

# create payout request
class PayoutRequestSerializer(serializers.Serializer):
    amount_in_paise = serializers.IntegerField(required=True)
    bank_account_id = serializers.CharField(required=True)
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