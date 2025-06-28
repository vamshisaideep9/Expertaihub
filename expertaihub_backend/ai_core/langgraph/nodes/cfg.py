from ai_core.config.loader import niche_cfg

TIER_MAX_DOCS = {"free": 8, "plus": 12, "pro+": 24}

def inject_cfg(state):
    ncfg = niche_cfg(state["niche"])
    tier = state.get("tier") or ncfg["default_tier"]
    tier = tier.lower()

    state.update(ncfg)                           # country & retriever_index

    index = state["retriever_index"]
    if tier == "plus":
        index += "_plus"
    elif tier == "pro+":
        index += "_proplus"
    state["retriever_index"] = index

    state["max_docs"] = TIER_MAX_DOCS[tier]      # tiny dict for now
    return state
