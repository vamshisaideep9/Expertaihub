# workflows/__init__.py

from .workflow_free import get_immigration_graph


def get_graph_for_tier(tier: str):
    """Return a compiled graph for the given membership tier."""
    tier = (tier or "free").lower()

    # Build the base immigration graph
    graph = get_immigration_graph()
    if tier == "plus":
        graph = get_immigration_graph()
    elif tier == "pro+":
        pass

    return graph
