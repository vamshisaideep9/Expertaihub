from django.urls import path
from .v1.views_free import FreeImmigrationAIView

urlpatterns = [
    path("immigration-ai/free/", FreeImmigrationAIView.as_view(), name="immigration-ai-free")
]