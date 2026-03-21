from django.urls import path
from . import views

app_name = 'verification'

urlpatterns = [
    path('request/', views.RequestVerificationView.as_view(), name='request_verification'),
    path('my-requests/', views.MyVerificationRequestsView.as_view(), name='my_requests'),
    path('pending/', views.PendingVerificationsView.as_view(), name='pending_verifications'),
    path('<int:pk>/verify/', views.VerifyDocumentView.as_view(), name='verify_document'),
    path('history/', views.VerificationHistoryView.as_view(), name='history'),
    path('list/', views.DocumentVerificationListView.as_view(), name='verification_list'),
    path('verify-by-id/', views.VerifyByIdView.as_view(), name='verify_by_id'),
]
