from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
app = Celery("expertaihub_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "monthly-uscode-title8-pdf": {
        "task": "ai_core.tasks.fetch_uscode_title8_pdf",
        "schedule": crontab(minute=0, hour=1, day_of_month=1),
    },
    "monthly-cfr-title8-vol1-pdf": {
        "task": "ai_core.tasks.fetch_cfr_title8_vol1_pdf",
        "schedule": crontab(minute=30, hour=1, day_of_month=1),
    },
}


app.conf.beat_schedule.update({
    # … your existing schedules …
    "monthly-federal-register-notices": {
        "task": "ai_core.tasks.fetch_federal_register_notices",
        "schedule": crontab(minute=0, hour=2, day_of_month=2),
    },
})


app.conf.beat_schedule.update({
    # … existing entries …
    "monthly-visa-bulletin": {
        "task": "ai_core.tasks.fetch_visa_bulletin",
        "schedule": crontab(minute=0, hour=6, day_of_month=1),
    },
})


app.conf.beat_schedule.update({
    # … existing tasks …
    "monthly-uscis-policy-manual": {
        "task": "ai_core.tasks.fetch_uscis_policy_manual",
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
    "daily-courtlistener-immigration-pdfs": {
        "task": "ai_core.tasks.fetch_courtlistener_immigration_pdfs",
        "schedule": crontab(hour=2, minute=30),
    },
})


app.conf.beat_schedule.update({
    # … other tasks …
    "monthly-immigration-law-advisor": {
        "task": "ai_core.tasks.fetch_immigration_law_advisor_pdfs",
        "schedule": crontab(minute=0, hour=6, day_of_month=1),
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
    "monthly-ca9-imm-outline-pdfs": {
        "task": "ai_core.tasks.fetch_ca9_immigration_outline_pdfs",
        "schedule": crontab(minute=0, hour=6, day_of_month=1),
    },
})

