import re
import hashlib
import spacy
from pathlib import Path
from typing import List, Dict, Any, Set
# import logging

# Load models
nlp = spacy.load("en_core_web_sm")

# US States map
US_STATES = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR", "CALIFORNIA": "CA",
    "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE", "FLORIDA": "FL", "GEORGIA": "GA",
    "HAWAII": "HI", "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA",
    "KANSAS": "KS", "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO",
    "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM", "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH",
    "OKLAHOMA": "OK", "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT",
    "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
}

# Extended immigration-specific labels (post-mapped from spaCy entities)
IMMIGRATION_ENTITY_LABELS = {
    "PERSON": ["PETITIONER_NAME", "BENEFICIARY_NAME", "SPONSOR_NAME", "NAME"],
    "ORG": ["EMPLOYER_NAME", "GOV_AGENCY", "SCHOOL_NAME"],
    "GPE": ["COUNTRY_OF_CITIZENSHIP", "COUNTRY_OF_BIRTH"],
    "DATE": ["DATE_OF_BIRTH", "FILING_DATE", "NATURALIZATION_DATE", "ENTRY_DATE"],
    "LAW": ["LAW_REFERENCE"],
    "NORP": ["CITIZENSHIP_STATUS", "ETHNICITY"],
}

# Allowed base types from spaCy
ALLOWED_ENTITY_LABELS = set(IMMIGRATION_ENTITY_LABELS.keys())



def extract_urls(text: str) -> List[str]:
    """
    Extracts all HTTP/HTTPS URLs from the given text.
    """
    url_pattern = re.compile(
        r"https?://[^\s\"'>)\]]+",  # match http or https up to next whitespace or closing bracket
        re.IGNORECASE
    )
    return url_pattern.findall(text)

# Removed logger setup

DOC_RULES = {
    "affidavit":             ["affidavit"],
    "application":           ["application", r"\bi[-_]?485\b", r"\bn[-_]?400\b"],
    "form":                  ["uscis form", r"\bform\s+i[-_]?\d+"],
    "petition":              ["petition", r"\bi[-_]?130\b"],
    "biometrics_notice":     ["biometrics appointment", "asc notice"],
    "request_for_evidence":  ["rfe", "request for evidence"],
    "notice":                ["notice of action", "i-797"],
    "waiver":                ["waiver", r"\bi[-_]?601\b"],
    "certificate":           ["certificate of naturalization", "certificate"],
    "guideline":             ["guidelines", "instruction"],
    "visa":                  ["visa approval", "visa interview", "ds-160"],
    "evidence":              ["supporting evidence", "proof", "documents submitted"],
    "correspondence":        ["email", "letter", "communication"],
    "receipt":               ["receipt number", "uscis received"],
    "contract":              ["employment contract", "agreement"],
    "authorization":         ["work authorization", "ead", r"\bi[-_]?766\b"],
    "contact_directory":     ["embassy directory", "embassy addresses", "parseapi", "back4app"],
    "court_decision": ["ocaho", "eoir", "bia precedent"]
}

# pre-compile regex patterns for speed
COMPILED: dict[str, List[re.Pattern]] = {
    label: [re.compile(pat, re.IGNORECASE) for pat in pats]
    for label, pats in DOC_RULES.items()
}

# --------------------------------------------------------------------
# 2. helper to test any text blob against map
# --------------------------------------------------------------------
def _match_label(blob: str) -> str | None:
    for label, patterns in COMPILED.items():
        if any(p.search(blob) for p in patterns):
            return label
    return None

# --------------------------------------------------------------------
# 3. public function
# --------------------------------------------------------------------
def classify_doc_type(text: str, file_path: str = "") -> str:
    """
    Decide doc_type by looking at:
    1) first 2k chars of content
    2) filename (stem)
    3) each folder name in the path
    Returns 'unknown' if no rule matches.
    """
    # --- 1. content ---
    label = _match_label(text[:2000])
    if label:
        return label

    # prepare pieces from the path
    path = Path(file_path)
    filename = path.stem.lower()
    folders  = [p.lower() for p in path.parts]

    # --- 2. filename ---
    label = _match_label(filename)
    if label:
        return label

    # --- 3. folder names (most specific last) ---
    for folder in reversed(folders):
        label = _match_label(folder)
        if label:
            return label

    return "unknown"

import re


def clean_category(raw: str) -> str:
    """Return a slug-safe, date-free category string."""
    no_dates = re.sub(r"[_\-]?\b(20\d{2})([_\-]?(0[1-9]|1[0-2]))?\b", "", raw)
    no_slashes = re.sub(r"[\\/]", "", no_dates)
    return no_slashes.strip().replace(" ", "")

def derive_jurisdiction_path(doc) -> List[str]:
    print(f"Deriving jurisdiction path for doc: {getattr(doc, 'id', 'unknown')}")
    path = [doc.country.name.upper()]

    # Attempt to extract state from path or content
    state_match = re.search(r"/([A-Z]{2})[_/]", doc.source_path.upper())
    state = None
    if state_match:
        state = state_match.group(1)
    else:
        text_snippet = doc.content[:3000].upper()
        for full_state, abbrev in US_STATES.items():
            if re.search(rf"\b({full_state}|STATE OF {full_state}|FILED IN {full_state}|{full_state} CODE)\b", text_snippet):
                state = abbrev
                break
    if state:
        path.append(state)

    # Clean category: remove date-like segments
    if doc.category:
        category = clean_category(doc.category)
        if category:
            path.append(category)

    print(f"Jurisdiction path: {path}")
    return path


def map_entity(ent, context: str) -> str:
    print(f"Mapping entity: {ent.text} ({ent.label_}) with context: {context}")
    label = ent.label_
    text = ent.text.strip().lower()
    mapping = IMMIGRATION_ENTITY_LABELS.get(label, [])

    if label == "PERSON":
        if "petitioner" in context.lower(): return "PETITIONER_NAME"
        if "beneficiary" in context.lower(): return "BENEFICIARY_NAME"
        if "sponsor" in context.lower(): return "SPONSOR_NAME"
        return "NAME"
    elif label == "ORG":
        if "school" in context.lower(): return "SCHOOL_NAME"
        if "uscis" in context.lower() or "immigration" in context.lower(): return "GOV_AGENCY"
        if "employer" in context.lower(): return "EMPLOYER_NAME"
        return "ORG"
    elif label == "GPE":
        return "COUNTRY_OF_CITIZENSHIP"
    elif label == "DATE":
        if "birth" in context.lower(): return "DATE_OF_BIRTH"
        if "filed" in context.lower(): return "FILING_DATE"
        return "DATE"
    elif label in IMMIGRATION_ENTITY_LABELS:
        return IMMIGRATION_ENTITY_LABELS[label][0]
    return label

def run_ner(text: str, context_window: int = 5) -> List[Dict[str, Any]]:
    print("Running NER on text.")
    print(f"Input text (truncated): {text[:100]}")
    doc = nlp(text)
    seen: Set[str] = set()
    entities: List[Dict[str, Any]] = []

    for ent in doc.ents:
        if ent.label_ not in ALLOWED_ENTITY_LABELS:
            continue
        entity_text = ent.text.strip()
        if len(entity_text) <= 1 or entity_text.lower() in {"a", "the"}:
            continue
        ent_key = f"{ent.label_}|{entity_text.lower()}"
        if ent_key in seen:
            continue
        seen.add(ent_key)

        start_token = max(ent.start - context_window, 0)
        end_token = min(ent.end + context_window, len(doc))
        context = doc[start_token:end_token].text.strip()

        refined_label = map_entity(ent, context)

        print(f"Entity found: {entity_text} ({ent.label_}) mapped to {refined_label}")
        entities.append({
            "label": refined_label,
            "text": entity_text,
            "start": ent.start_char,
            "end": ent.end_char,
            "context": context,
        })

    print(f"Total entities extracted: {len(entities)}")
    return entities

def compute_version_hash(text: str) -> str:
    print("Computing version hash.")
    return hashlib.sha256(text.encode()).hexdigest()


from urllib.parse import urlparse
def extract_domains(urls: List[str]) -> List[str]:
    domains = [urlparse(u).netloc.lower() for u in urls if urlparse(u).netloc]
    return sorted(set(domains))


def clean_ner_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        ent for ent in entities
        if len(ent["text"]) > 2
        and not re.search(r"[^a-zA-Z0-9\s.,&\-]", ent["text"])  # filter non-readable
        and not ent["text"].lower().startswith(("json", "print", "load"))
    ]