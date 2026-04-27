from django.contrib import admin

# Register your models here.
from .models import Merchant, Ledger, Payout

class MerchantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'avaliable_balance_in_paise', 'created_at', 'updated_at')
    search_fields = ('id', 'name',)
    readonly_fields = ('id',)

class LedgerAdmin(admin.ModelAdmin):
    list_display = ('merchant_id', 'amount_in_paise', 'entry_type', 'refrence_id', 'created_at', 'updated_at')
    search_fields = ('merchant_id', 'entry_type',)
    readonly_fields = ('id',)

class PayoutAdmin(admin.ModelAdmin):
    list_display = ('merchant_id', 'amount_in_paise', 'status', 'idempotency_key', 'created_at', 'updated_at')
    search_fields = ('merchant_id', 'status',)
    readonly_fields = ('id',)

admin.site.register(Merchant)
admin.site.register(Ledger)
admin.site.register(Payout)