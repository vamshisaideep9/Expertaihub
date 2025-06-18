from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("suggestions", "0002_faqquestion_embedding"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="faqquestion",
            name="embedding",
        ),
        migrations.RemoveField(
            model_name="chatsuggestion",
            name="embedding",
        ),
    ]
