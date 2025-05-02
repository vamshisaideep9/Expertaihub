from django.urls import path
from .views import MembershipDetailView, MembershipListAPIView, MothlyUsageListApiView

urlpatterns = [
    path("membership/", MembershipDetailView.as_view(), name="membership-detail"),
    path("membership/all/", MembershipListAPIView.as_view(), name="membership-list"),
    path("monthly-usage/all/", MothlyUsageListApiView.as_view(), name="monthlyusage-list")
] 
