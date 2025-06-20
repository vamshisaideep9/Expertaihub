from celery import Celery
from celery.schedules import crontab
import os
import platform

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
app = Celery("expertaihub_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Windows-specific configuration
if platform.system().lower() == "windows":
    app.conf.update(
        task_always_eager=False,
        task_eager_propagates=True,
        worker_pool_restarts=True,
        worker_pool='solo',  # Use solo pool on Windows
        worker_concurrency=1,  # Single worker process
    )



NIGHTLY = crontab(minute=34, hour=0)


app.conf.beat_schedule = {
    "visa-bulletin": {
        "task": "ai_core.tasks.fetch_visa_bulletin",
        "schedule": crontab(minute=0, hour=1, day_of_month=1),
    },
    "uscis-policy-manual": {
        "task": "ai_core.tasks.fetch_uscis_policy_manual",
        "schedule": NIGHTLY,
    },
    "uscis-policy-memos": {
        "task": "ai_core.tasks.fetch_uscis_policy_memos",
        "schedule": NIGHTLY,
    },
    "uscis-news-releases": {
        "task": "ai_core.tasks.fetch_uscis_news_releases",
        "schedule": NIGHTLY,
    },
    "uscis-alerts": {
        "task": "ai_core.tasks.fetch_uscis_alerts",
        "schedule": NIGHTLY,
    },
    "build-faq-index": {
        "task": "suggestions.tasks.build_faq_index",
        "schedule": NIGHTLY,
    },
}
