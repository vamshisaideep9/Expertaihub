from django.urls import path
from api.views import ImmigrationAIView

urlpatterns = [
    path("api/immigration-ai/", ImmigrationAIView.as_view(), name="immigration-ai"),
]