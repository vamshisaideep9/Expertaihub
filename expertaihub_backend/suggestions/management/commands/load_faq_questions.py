from pathlib import Path
import json
from django.core.management.base import BaseCommand, CommandError
from suggestions.models import FAQQuestion


class Command(BaseCommand):
    help = "Load FAQQuestion entries from a JSON fixture"

    def add_arguments(self, parser):
        default_path = Path(__file__).resolve().parents[2] / "fixtures" / "faq_questions.json"
        parser.add_argument(
            "--file",
            type=str,
            default=str(default_path),
            help="Path to JSON fixture (default: suggestions/fixtures/faq_questions.json)",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"Fixture not found: {path}")

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        created = 0
        for item in data:
            text = item.get("fields", {}).get("text") or item.get("text")
            if not text:
                continue
            _, is_new = FAQQuestion.objects.get_or_create(text=text)
            if is_new:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Loaded {created} FAQ questions"))
