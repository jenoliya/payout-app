from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status

# models
from django.contrib.auth.models import User
from .models import Merchant, Payout, Ledger

# serializers
from .serializers import PayoutRequestSerializer, LedgerSerializer, PayoutSerilaizer
    
class CreatePayoutRequestView(APIView):
    serializer_class = PayoutRequestSerializer  
    def post(self, request):
        # get idempotency key from header
        idempotency_key = request.headers.get('Idempotency-key')
        print("idempotency_key",request.headers.get('Idempotency-key'))
        input = {
            "idempotency_key": idempotency_key,
            "amount_in_paise": request.data['amount_in_paise'],
            "bank_account_id": request.data['bank_account_id']
        }
        if not input['idempotency_key']:
            return Response({"message": "Idempotency key is required"}, status=status.HTTP_400_BAD_REQUEST)
        print("input", input)
        serializer = self.serializer_class(data=input)
        serializer.is_valid(raise_exception=True)
        # get logged in user info
        user = User.objects.filter(id=request.user.id).first()
        merchant = Merchant.objects.filter(user=user.id).first()
        if not merchant:
            return Response({"message": "Merchant account does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        # check avalibale balance
        if serializer.validated_data['amount_in_paise'] > merchant.avaliable_balance_in_paise:
            return Response({"message": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
        # check idempotency key
        if Payout.objects.filter(idempotency_key=serializer.validated_data['idempotency_key']).exists():
            # return theexisting record
            payout = Payout.objects.filter(idempotency_key=serializer.validated_data['idempotency_key']).first()
        # create payout request
        payout = Payout.objects.create(
            merchant_id = merchant,
            amount_in_paise = serializer.validated_data['amount_in_paise'],
            status = "pending",
            idempotency_key = serializer.validated_data['idempotency_key']
        )
        output={
            "message": "Payout request received",
            "payout": payout.id
        }
        return Response(output, status=status.HTTP_201_CREATED)
    

class ProcessPayoutRequestView(APIView):
    def get(self, request, id):
        # get payout request
        payout = Payout.objects.filter(id=id).first()
        if not payout:
            return Response({"message": "Payout request does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        # update payout request
        payout.status = "processed"
        payout.save()
        # to do : update merchant balance
        merchant = Merchant.objects.filter(id=payout.merchant_id.id).first()
        if not merchant:
            return Response({"message": "Merchant account does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        merchant.avaliable_balance_in_paise = merchant.avaliable_balance_in_paise + payout.amount_in_paise
        merchant.save()
        # to do : create ledger
        ledger = Ledger.objects.create(
            merchant_id = merchant,
            amount_in_paise = payout.amount_in_paise,
            entry_type = "credit",
            refrence_id = payout.id
        )
        output={
            "message": "Payout request processed",
            "payout": payout.id
        }
        return Response(output, status=status.HTTP_200_OK)
    
# merchant payout history
class GetMerchantPayoutHistoryView(APIView):
    def get(self, request):

        if not request.user.is_authenticated:
            return Response(
                {"message": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        merchant = Merchant.objects.filter(user=request.user).first()

        if not merchant:
            return Response(
                {"message": "Merchant not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # correct filtering
        payouts = Payout.objects.filter(merchant_id=merchant.id)

        # use serializer directly
        serializer = PayoutSerilaizer(payouts, many=True)

        output = {
            "message": "Payout list",
            "payout_list": serializer.data
        }

        return Response(output, status=status.HTTP_200_OK)
    
# merchant transaction history 
class GetMerchantTransactionHistoryView(APIView):
    def get(self, request):

        if not request.user.is_authenticated:
            return Response(
                {"message": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        merchant = Merchant.objects.filter(user=request.user).first()

        if not merchant:
            return Response(
                {"message": "Merchant not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # correct filtering
        ledgers = Ledger.objects.filter(merchant_id=merchant.id)

        # use serializer directly
        serializer = LedgerSerializer(ledgers, many=True)

        output = {
            "message": "Ledger list",
            "ledger_list": serializer.data
        }

        return Response(output, status=status.HTTP_200_OK)