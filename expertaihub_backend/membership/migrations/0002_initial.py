# Generated by Django 5.2 on 2025-05-02 08:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('membership', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='membership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='monthlyusage',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_usage', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='monthlyusage',
            unique_together={('user', 'period')},
        ),
    ]
