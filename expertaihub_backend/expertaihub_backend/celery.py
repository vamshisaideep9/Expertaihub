from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
app = Celery("expertaihub_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule.update({
    "monthly-visa-bulletin": {
        "task": "ai_core.tasks.fetch_visa_bulletin",
        "schedule": crontab(minute=0, hour=6, day_of_month=1),
    },
})


app.conf.beat_schedule.update({
    # … existing tasks …
    "monthly-uscis-policy-manual": {
        "task": "ai_core.tasks.fetch_uscis_policy_manual",
        "schedule": crontab(minute=0, hour=3, day_of_week="mon"),
    },
    
})


app.conf.beat_schedule.update({
    # … existing tasks …
    "monthly-uscis-policy-manual": {
        "task": "ai_core.tasks.fetch_uscis_policy_memos",
        "schedule": crontab(minute=0, hour=3, day_of_month=1),
    },
    
})



app.conf.beat_schedule.update({
    # … existing tasks …
    "monthly-bia-decisions": {
        "task": "ai_core.tasks.fetch_bia_decisions",
        "schedule": crontab(minute=0, hour=5, day_of_month=2),
    },
})





app.conf.beat_schedule.update({
    # … your existing schedules …
    "daily-immigration-impact": {
        "task": "ai_core.tasks.fetch_immigration_impact_article",
        "schedule": crontab(minute=5, hour=0),
    },
})




app.conf.beat_schedule.update({
    "daily-uscis-news-releases": {
        "task": "ai_core.tasks.fetch_uscis_news_releases",
        # every day at 3:00 AM Asia/Kolkata
        "schedule": crontab(hour=3, minute=0),
    },
})



app.conf.beat_schedule.update({
    "daily-uscis-alerts": {
        "task": "ai_core.tasks.fetch_uscis_alerts",
        "schedule": crontab(hour=3, minute=0),
    },
})

