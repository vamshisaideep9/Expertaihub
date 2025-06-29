import pytest

pytest.importorskip("django")

import os
import json
import tempfile
from pathlib import Path
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import Mock, patch

from . import views

class DocumentDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.original_base = views.BASE_DOCUMENTS_FOLDER
        views.BASE_DOCUMENTS_FOLDER = self.tmpdir.name

    def tearDown(self):
        views.BASE_DOCUMENTS_FOLDER = self.original_base

    def _create_doc(self, niche="immigration", country="usa", form="i-130"):
        folder = Path(self.tmpdir.name) / f"{niche}_docs" / country / form
        folder.mkdir(parents=True)
        with open(folder / "metadata.json", "w") as f:
            json.dump({"name": "test"}, f)
        with open(folder / "sample.pdf", "wb") as f:
            f.write(b"%PDF-1.4 test")

    def test_document_detail_valid_path(self):
        self._create_doc()
        url = reverse("document-detail", kwargs={"niche": "immigration", "country": "usa", "form_number": "i-130"})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["name"], "test")
        self.assertIn("download_url", data)

    def test_document_detail_invalid_path(self):
        url = reverse(
            "document-detail",
            kwargs={"niche": "immigration", "country": "usa", "form_number": "..secret"},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)


class RetrieveContextErrorTests(TestCase):
    def test_retriever_exception_sets_empty_docs(self):
        from ai_core.langgraph.nodes import nodes as node_module
        state = {"question": "hi", "session_id": "s1"}

        mock_retriever = Mock()
        mock_retriever.invoke.side_effect = Exception("boom")

        with patch.object(node_module, "get_retriever", return_value=mock_retriever):
            result = node_module.retrieve_context(state)

        self.assertEqual(result["docs"], [])
