from pgvector.django import CosineDistance

from .models import FAQQuestion


def top5_related(query_vec):
    """Return up to five FAQ question texts closest to query_vec."""
    qs = (
        FAQQuestion.objects.annotate(
            dist=CosineDistance("embedding", query_vec)
        )
        .order_by("dist")
        .values_list("text", flat=True)[:5]
    )
    return list(qs)
