from pathlib import Path

from django.core.management.base import BaseCommand
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from suggestions.models import FAQQuestion


class Command(BaseCommand):
    help = "Build or update the FAISS index of FAQQuestion embeddings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--device",
            type=str,
            default="cpu",
            help="Device for embeddings ('cpu' or 'cuda')",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=512,
            help="Batch size for embedding",
        )

    def handle(self, *args, **options):
        device = options["device"]
        batch_size = options["batch_size"]

        index_dir = Path("suggestions/vectorstores/free")
        index_dir.mkdir(parents=True, exist_ok=True)

        embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": device},
            encode_kwargs={"batch_size": batch_size},
        )

        index_path = index_dir / "index.faiss"
        if index_path.exists():
            self.stdout.write(self.style.NOTICE("Loading existing index"))
            vs = FAISS.load_local(
                str(index_dir),
                embedder,
                allow_dangerous_deserialization=True,
            )
            existing_ids = {
                int(doc.metadata.get("id"))
                for doc in vs.docstore._dict.values()
            }
        else:
            vs = None
            existing_ids = set()
            self.stdout.write(self.style.NOTICE("No existing index found"))

        qs = FAQQuestion.objects.exclude(id__in=existing_ids).order_by("id")
        if qs.exists():
            self.stdout.write(f"Embedding {qs.count()} new questions")
        else:
            self.stdout.write("No new questions to embed")

        docs = [Document(page_content=q.text, metadata={"id": q.id}) for q in qs]

        if docs:
            if vs is None:
                vs = FAISS.from_documents(docs, embedder)
            else:
                new_vs = FAISS.from_documents(docs, embedder)
                vs.merge_from(new_vs)

            vs.save_local(str(index_dir))
            self.stdout.write(self.style.SUCCESS("Saved FAISS index"))
        else:
            self.stdout.write(self.style.WARNING("Index not updated"))
