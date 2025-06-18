from django.db import migrations
from pgvector.django import VectorField


class Migration(migrations.Migration):

    dependencies = [
        ("suggestions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="faqquestion",
            name="embedding",
            field=VectorField(dim=768, null=True),
        ),
    ]
