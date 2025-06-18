import pytest

pytest.importorskip("django")

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from chats.models import ChatSession
from suggestions.models import ChatSuggestion


class StreamSuggestionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(
            email="user@example.com", full_name="User", password="pw", is_active=True
        )
        self.client.force_authenticate(self.user)
        self.session = ChatSession.objects.create(user=self.user, slug="test-session")

    @patch("chats.views.graph.invoke")
    def test_stream_stores_related_queries(self, mock_invoke):
        mock_invoke.return_value = {
            "answer": "Done",
            "related_queries": [f"Q{i}" for i in range(5)],
        }

        url = reverse("chats:chat-session-stream", args=[self.session.slug])
        resp = self.client.post(url, {"question": "Hi"}, format="json")
        self.assertEqual(resp.status_code, 200)

        suggestions = ChatSuggestion.objects.filter(session=self.session)
        self.assertEqual(suggestions.count(), 5)

        body = b"".join(resp.streaming_content).decode()
        self.assertIn("Q0", body)

    @patch("chats.views.graph.invoke")
    def test_stream_does_not_duplicate_suggestions(self, mock_invoke):
        mock_invoke.return_value = {
            "answer": "Ok",
            "related_queries": ["A", "B", "C"],
        }

        url = reverse("chats:chat-session-stream", args=[self.session.slug])
        resp = self.client.post(url, {"question": "Hi"}, format="json")
        self.assertEqual(resp.status_code, 200)

        suggestions = ChatSuggestion.objects.filter(session=self.session)
        self.assertEqual(suggestions.count(), 3)
        for text in ["A", "B", "C"]:
            self.assertEqual(
                ChatSuggestion.objects.filter(session=self.session, text=text).count(),
                1,
            )
