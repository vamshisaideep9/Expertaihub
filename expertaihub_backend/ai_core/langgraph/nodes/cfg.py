from ai_core.config.loader import niche_cfg

TIER_MAX_DOCS = {"free": 8, "plus": 12, "pro+": 24}

def inject_cfg(state):
    ncfg = niche_cfg(state["niche"])
    tier = tier.lower()
    tier = state.get("tier") or ncfg["default_tier"]

    state.update(ncfg)                           # country & retriever_index
    state["max_docs"] = TIER_MAX_DOCS[tier]      # tiny dict for now
    return state