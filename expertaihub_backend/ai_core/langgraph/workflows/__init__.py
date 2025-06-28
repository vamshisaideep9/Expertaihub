from .workflow_free import get_immigration_graph


def get_graph_for_tier(tier: str):
    """Return a compiled graph for the given membership tier."""
    tier = (tier or "free").lower()

    # Build the base immigration graph
    graph = get_immigration_graph()

    # Placeholder for tier-specific customization
    if tier == "plus":
        # Future: add nodes/features for Plus tier
        pass
    elif tier == "pro+":
        # Future: add nodes/features for Pro+ tier
        pass

    return graph
