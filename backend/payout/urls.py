from django.urls import path

from .import views

urlpatterns = [
    # payout request
    path('request/', views.CreatePayoutRequestView.as_view(), name='create-payout-request'),
    # payout process
    path('process/<int:id>/', views.ProcessPayoutRequestView.as_view(), name='process-payout-request'),
    # get incomplete payout requests
    path('list/', views.GetPayoutRequestView.as_view(), name='get-payout-request'),
]

# urlpatterns = [
#     path('payout/', views, name='index'),
#     path('payout/', views.payout, name='payout'),
# ]

# urlpatterns = [
#     # student
#     path('student/list/', views.StudentView.as_view(), name='student-list'),
#     path('student/create/', views.StudentView.as_view(), name='create-student'),
#     path('student/<int:id>/update/', views.StudentView.as_view(), name='update-student'),
#     path('student/<int:id>/delete/', views.StudentView.as_view(), name='delete-student'),
# ]