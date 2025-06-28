from django.core.management.base import BaseCommand
from ai_core.models import RawDocument
from immigration.usa.ml import (
    classify_doc_type,
    derive_jurisdiction_path,
    run_ner,
    compute_version_hash,
    extract_urls, extract_domains, clean_ner_entities
)

class Command(BaseCommand):
    help = "Backfill a single document's metadata by ID"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Force reprocessing even if version_hash exists")

    def handle(self, *args, **options):
        force = options["force"]
        docs = RawDocument.objects.all()

        if not docs.exists():
            self.stdout.write(self.style.WARNING(f"❌ No document found"))
            return

        for doc in docs:
            try:
                if force or "version_hash" not in doc.metadata:
                    self.stdout.write(self.style.SUCCESS(f"🛠 Processing document {doc.id}"))
                    doc_type = classify_doc_type(doc.content, doc.filename)
                    jurisdiction_path = derive_jurisdiction_path(doc)
                    version_hash = compute_version_hash(doc.content)
                    ner_entities = clean_ner_entities(run_ner(doc.content[:5000]))
                    urls = list(set(extract_urls(doc.content)))
                    domains = list(set(extract_domains(urls)))

                    doc.metadata.update({
                        "doc_type": doc_type,
                        "jurisdiction_path": jurisdiction_path,
                        "version_hash": version_hash,
                        "ner_entities": ner_entities,
                        "urls": urls,
                        "domains": domains
                    })
                    doc.save(update_fields=["metadata"])
                    self.stdout.write(self.style.SUCCESS(f"✅ Document {doc.id} metadata saved"))
                else:
                    self.stdout.write(self.style.NOTICE(f"⏭ Document {doc.id} already has version_hash. Use --force to overwrite."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"💥 Error processing document {getattr(doc, 'id', 'unknown')}: {e}"))
