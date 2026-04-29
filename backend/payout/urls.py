from django.urls import path

# views
from .import views

urlpatterns = [
    # payout request
    path('request/', views.CreatePayoutRequestView.as_view(), name='create-payout-request'),
    # payout process
    path('process/<int:id>/', views.ProcessPayoutRequestView.as_view(), name='process-payout-request'),
    # get merchant transaction history
    path('history/', views.GetMerchantTransactionHistoryView.as_view(), name='get-merchant-transaction-history'),
]