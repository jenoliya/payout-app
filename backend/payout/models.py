from django.db import models
from uuid import uuid4

from django.contrib.auth.models import User

# Create your models here.
class Merchant(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE, null = True)
    name = models.CharField(max_length=250)
    avaliable_balance_in_paise = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.name)
    
class Ledger(models.Model):
    ENTRY_TYPES = [
        ("credit", "credit"),
        ("hold", "hold"),
        ("debit", "debit"),
        ("refund", "refund"),
    ]
    merchant_id = models.ForeignKey(Merchant, on_delete = models.CASCADE, null = True)
    amount_in_paise = models.IntegerField(default=0)
    entry_type = models.CharField(max_length = 20, choices = ENTRY_TYPES)
    refrence_id = models.UUIDField(default = uuid4, editable = False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.merchant_id)
        
class Payout(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("processing", "processing"),
        ("completed", "completed"),
        ("failed", "failed"),
    ]
    merchant_id = models.ForeignKey(Merchant, on_delete = models.CASCADE, null = True)
    amount_in_paise = models.IntegerField(default=0)
    status = models.CharField(max_length = 20, choices = STATUS_CHOICES)
    idempotency_key = models.CharField()
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.merchant_id)