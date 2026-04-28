from celery import shared_task
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import random

# models
from payout.models import Payout, Merchant, Ledger

# print current time
@shared_task(bind = True)
def print_current_time(self):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("current time : " + current_time)
    return current_time

# process pending payouts
@shared_task(bind = True)
def process_pending_payouts(self):   
    # filter records with pending status
    payouts = Payout.objects.filter(status="pending")

    # loop all selected records
    for payout in payouts:
        with transaction.atomic():
            # update payout status as processing
            payout.status = "processing"
            payout.save()

            # merchant.avaliavble_balance_in_paise - payout.amount_in_paise [= hold balance]
            merchant = Merchant.objects.filter(id=payout.merchant_id.id).first()
            if not merchant:
                return Response({"message": "Merchant account does not exist"}, status=status.HTTP_400_BAD_REQUEST)
            merchant.avaliable_balance_in_paise = merchant.avaliable_balance_in_paise - payout.amount_in_paise
            merchant.save()
# process holding payouts
@shared_task(bind = True)
def process_holdings_payouts(self):
    # filter records with processing status
    payouts = Payout.objects.filter(status="processing")

    # loop all selected records
    for payout in payouts:
        with transaction.atomic():

            # call payment gateway functions
            payment_process_status = random.random() < 0.7   # 70% Succeed
            if not payment_process_status:
                payout.status = "failed"
                payout.save()
                merchant = Merchant.objects.filter(id=payout.merchant_id.id).first()
                if merchant:
                    merchant.avaliable_balance_in_paise = merchant.avaliable_balance_in_paise + payout.amount_in_paise
                    merchant.save()
            else:

                # add record to ledger
                ledger = Ledger.objects.create(
                    merchant_id = payout.merchant_id,
                    amount_in_paise = payout.amount_in_paise,
                    entry_type = "credit",
                    refrence_id = payout.id
                )
                # update payout status either completed or failed                
                payout.status = "completed"
                payout.save()
