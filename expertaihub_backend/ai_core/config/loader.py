from functools import lru_cache
from django.apps import apps

@lru_cache(maxsize=256)
def niche_cfg(slug_or_id: str) -> dict:
    Advisor = apps.get_model("ai_core", "Advisor")
    adv = Advisor.objects.select_related("country").get(slug=slug_or_id)
    return {
        "country"        : adv.country.name.lower() if adv.country else "usa",
        "retriever_index": adv.retriever_index,
        "default_tier"   : adv.default_tier,
    }