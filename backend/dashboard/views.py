from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum

# models
from payout.models import Merchant, Payout, Ledger

# views
from payout.views import GetMerchantTransactionHistoryView, GetMerchantPayoutHistoryView

# get user dashboard
class GetDashboardView(APIView):
    def get(self, request):

        if not request.user.is_authenticated:
            return Response(
                {"message": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # get merchant
        merchant = Merchant.objects.filter(user=request.user).first()

        if not merchant:
            return Response(
                {"message": "Merchant account does not exist"},
                status=status.HTTP_400_BAD_REQUEST
            )

         # HOLD = pending + processing payouts
        hold_balance = Payout.objects.filter(
            merchant_id=merchant.id,
            status__in=["pending", "processing"]
        ).aggregate(total=Sum("amount_in_paise"))["total"] or 0

        # AVAILABLE = total ledger - hold
        total_balance = Ledger.objects.filter(
            merchant_id=merchant.id
        ).aggregate(total=Sum("amount_in_paise"))["total"] or 0

        # merchant transaction history
        transaction_history = GetMerchantTransactionHistoryView().get(request).data
        payout_history = GetMerchantPayoutHistoryView().get(request).data

        output = {
            "message": "Dashboard",
            "available_balance": merchant.avaliable_balance_in_paise,
            "hold_balance": hold_balance,
            "name": merchant.name,
            "email": merchant.user.email,
            **transaction_history,
            **payout_history
        }

        return Response(output, status=status.HTTP_200_OK)