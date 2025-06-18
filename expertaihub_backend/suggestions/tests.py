import tempfile
from pathlib import Path

from django.test import SimpleTestCase
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from suggestions import utils


class Top5RelatedTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.original_index_dir = utils.INDEX_DIR
        utils.load_faq_vectorstore.cache_clear()
        utils.INDEX_DIR = Path(self.tmp.name)

        embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        docs = [
            Document(page_content="visa application process"),
            Document(page_content="how to apply for a visa"),
            Document(page_content="immigration visa types"),
            Document(page_content="how to file taxes"),
            Document(page_content="best pizza toppings"),
            Document(page_content="study visa requirements"),
        ]
        vs = FAISS.from_documents(docs, embedder)
        vs.save_local(self.tmp.name)

    def tearDown(self):
        utils.load_faq_vectorstore.cache_clear()
        utils.INDEX_DIR = self.original_index_dir

    def test_top5_ordering(self):
        results = utils.top5_related("visa application")
        self.assertTrue(results)
        self.assertEqual(results[0], "visa application process")
        self.assertIn("how to apply for a visa", results)
        self.assertLessEqual(len(results), 5)
