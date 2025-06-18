import logging
from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

@shared_task
def build_faq_index():
    """Run the build_faq_index management command."""
    logger.info("Starting build_faq_index command")
    try:
        call_command("build_faq_index")
    except Exception as exc:
        logger.exception("build_faq_index command failed")
        raise exc
    logger.info("build_faq_index command completed successfully")
    return "FAQ index built"
