import pytest

pytest.importorskip("django")

from django.urls import include, path

urlpatterns = [
    path('api/', include('ai_core.urls')),
    path('api/', include('chats.urls')),
]
