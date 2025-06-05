from django.urls import path
from .views import MembershipDetailView, MembershipListAPIView, MonthlyUsageView

urlpatterns = [
    path("membership/", MembershipDetailView.as_view(), name="membership-detail"),
    path("membership/all/", MembershipListAPIView.as_view(), name="membership-list"),
    path('monthly-usage/', MonthlyUsageView.as_view(), name='monthly-usage'),
]

