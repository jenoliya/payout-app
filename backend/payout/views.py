from django.shortcuts import render
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status

# models
from django.contrib.auth.models import User
from .models import Merchant, Payout, Ledger

# serializers
from .serializers import PayoutRequestSerializer

# Create your views here.
# class MerchantView(APIView):
#     serializer_class = MerchantSerializer
#     def get(self, request):
#         # select records from merchants model
#         merchants = Merchant.objects.all()
#         # serialize merchants
#         serializer = self.serializer_class(merchants, many=True)
#         output = {
#             "message" : "Merchant list",
#             "merchant_list": serializer.data
#         }
#         return Response(output, status=status.HTTP_200_OK)
    
class CreatePayoutRequestView(APIView):
    serializer_class = PayoutRequestSerializer  
    def post(self, request):
        # print(request.data)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # get logged in user info
        user = User.objects.filter(id=request.user.id).first()
        print("user", user)
        merchant = Merchant.objects.filter(user=user.id).first()
        print("merchant", merchant)
        if not merchant:
            return Response({"message": "Merchant account does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        # check avalibale balance
        if serializer.validated_data['amount_in_paise'] > merchant.avaliable_balance_in_paise:
            return Response({"message": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
        # check idempotency key
        print("idempotency_key",serializer.validated_data['idempotency_key'])
        if Payout.objects.filter(idempotency_key=serializer.validated_data['idempotency_key']).exists():
            return Response({"message": "Idempotency key already exists"}, status=status.HTTP_400_BAD_REQUEST)
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
    
# get incomplete payout requests
class GetPayoutRequestView(APIView):
    def get(self, request):
        # select records from payout model
        payouts = Payout.objects.filter(status="pending")
        # serialize payouts
        serializer = self.serializer_class(payouts, many=True)
        output = {
            "message" : "Payout list",
            "payout_list": serializer.data
        }
        return Response(output, status=status.HTTP_200_OK)