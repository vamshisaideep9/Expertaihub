from django.urls import path
from .views import DocumentListAPIView, DocumentDetailAPIView, AdvisorListCreateView, CountryListCreateView

urlpatterns = [
    path('documents/<str:niche>/<str:country>/', DocumentListAPIView.as_view(), name='document-list'),
    path('documents/<str:niche>/<str:country>/<str:form_number>/', DocumentDetailAPIView.as_view(), name='document-detail'),
    path('advisor/', AdvisorListCreateView.as_view(), name ="advisor"),
    path('country/', CountryListCreateView.as_view(), name="country")
]
