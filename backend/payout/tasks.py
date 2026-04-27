from celery import shared_task
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status

# models
from payout.models import Payout, Merchant, Ledger

@shared_task(bind = True)
def print_current_time(self):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("current time : " + current_time)
    return current_time

# function to loop all the processing in payout model in time schedule of 60 secs
@shared_task(bind = True)
def process_payouts(self):    
    # select records from payout model
    payouts = Payout.objects.filter(status="pending")

    for payout in payouts:
        # update payout request
        # to do : update merchant balance
        merchant = Merchant.objects.filter(id=payout.merchant_id.id).first()
        if not merchant:
            return Response({"message": "Merchant account does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        merchant.avaliable_balance_in_paise = merchant.avaliable_balance_in_paise - payout.amount_in_paise
        merchant.save()
        payout.status = "completed"
        payout.save()
        # to do : create ledger
        ledger = Ledger.objects.create(
            merchant_id = merchant,
            amount_in_paise = payout.amount_in_paise,
            entry_type = "credit",
            refrence_id = payout.id
        )