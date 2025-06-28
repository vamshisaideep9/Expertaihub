#!/usr/bin/env python
"""
ai_core/pipeline/chunk_and_save.py
──────────────────────────────────
Chunks RawDocument → DocumentChunk with lean metadata.
"""

from __future__ import annotations
import os, sys, re, logging, django
from datetime import datetime
from django.db import transaction
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib
from django.utils import timezone
from pathlib import Path

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def now_iso() -> str:
    return timezone.now().isoformat(timespec="seconds").replace("+00:00", "Z")

# ── Django bootstrap ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
django.setup()

from django.conf import settings                     # noqa: E402
from ai_core.models import RawDocument, DocumentChunk # noqa: E402

# ── constants ───────────────────────────────────────────────────
CHUNK_SIZE    = 1_000
CHUNK_OVERLAP =   200


# ── logging ─────────────────────────────────────────────────────
log = logging.getLogger("chunk_and_save")
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))

# ═══════════════════════════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════════════════════════

# 🔄  ONE consolidated list of keywords
KEY_TERMS = (
    # signature / caption cues
    "dated", "date:", "decided", "issued", "entered", "signed",
    "executed", "adopted", "approved", "promulgated", "enacted",
    "filed", "recorded", "registered", "certified",

    # order / designation cues
    "ordered", "order dated", "designation dated", "designated",

    # update / version cues
    "last updated", "updated", "recently updated", "current as of",
    "revised", "revision date", "amended", "modified",

    # effectiveness cues
    "effective", "effective date", "effective as of",
    "in effect on", "comes into force",

    # publication / release cues
    "published", "released", "released on", "made public",

    # generic "date" labels sometimes used in forms
    "date of signature", "date signed", "signature date"
)


MONTH_NAME = r"(?:January|February|March|April|May|June|July|August|" \
             r"September|October|November|December)"
DATE_PATTERNS = [
    # 1) 15th day of November, 1989  |  This 2nd day of March, 2001
    rf"\b(?:on\s+the\s+|this\s+)?(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?{MONTH_NAME},\s*\d{{4}}\b",

    # 2) 15th November 1989 (ordinal, no 'day of')
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{MONTH_NAME}\s*,?\s*\d{{4}}\b",

    # 3) 15 Nov 1989  |  Nov 15 1989  |  1989-Nov-15
    rf"\b(\d{{1,2}}|\d{{4}})[-/\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/\s](\d{{1,2}}|\d{{2,4}})\b",

    # 4) November 15, 1989  (normal long form)
    rf"\b{MONTH_NAME}\s+\d{{1,2}},\s*\d{{4}}\b",

    # 5) Month only + year  (November 1989)
    rf"\b{MONTH_NAME}\s+\d{{4}}\b",

    # 6) 1989-11-15  or  2025_12_31
    r"\b(\d{4})[-_](\d{2})[-_](\d{2})\b",

    # 7) 12/31/1989 or 12/31/89  (allow two-digit year)
    r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b",
]


TOP_N, BOT_N = 3_000, 3_000

# ───────── helpers ──────────────────────────────────────────────
def _to_iso(m: re.Match) -> str | None:
    g = m.groups()
    try:
        if len(g) == 3 and len(g[0]) == 4:                   # yyyy-mm-dd
            return f"{g[0]}-{g[1]}-{g[2]}"
        if len(g) == 3 and g[2].isdigit():                   # m/d/yyyy
            return f"{g[2]}-{int(g[0]):02d}-{int(g[1]):02d}"
        return datetime.strptime(m.group(0), "%B %d, %Y").date().isoformat()
    except Exception:
        return None

def _line_with_key(lines: list[str]) -> str | None:
    """Return first line (bottom-up) that starts with any KEY_TERMS."""
    for line in reversed(lines):
        if any(line.lower().strip().startswith(k) for k in KEY_TERMS):
            return line
    return None

# ───────── main extractor ───────────────────────────────────────
def first_iso_date(text: str, *, last_modified_fallback: str | None = None) -> str | None:
    """
    Order:
    1. Bottom banner / signature lines with KEY_TERMS.
    2. Top banner / header with KEY_TERMS.
    3. Latest date anywhere in doc.
    4. Fallback to last_modified.
    """
    # 1️⃣ bottom
    bottom = text[-BOT_N:]
    if (line := _line_with_key(bottom.splitlines())):
        for pat in DATE_PATTERNS:
            if (m := re.search(pat, line, re.I)):
                if (iso := _to_iso(m)):
                    return iso
    for pat in DATE_PATTERNS:                               # banner without prefix
        if (m := re.search(pat, bottom, re.I)):
            if (iso := _to_iso(m)):
                return iso

    # 2️⃣ top
    top = text[:TOP_N]
    if (line := _line_with_key(top.splitlines())):
        for pat in DATE_PATTERNS:
            if (m := re.search(pat, line, re.I)):
                if (iso := _to_iso(m)):
                    return iso
    for pat in DATE_PATTERNS:
        if (m := re.search(pat, top, re.I)):
            if (iso := _to_iso(m)):
                return iso

    # 3️⃣ latest date anywhere (reverse scan)
    for pat in DATE_PATTERNS:
        if (m := re.search(pat, text[::-1], re.I)):
            span = len(text) - m.end(), len(text) - m.start()
            fwd  = text[span[0]:span[1]]
            m2 = re.match(pat, fwd, re.I)
            if m2:
                if (iso := _to_iso(m2)):
                    return iso

    # 4️⃣ fallback
    return (last_modified_fallback or "")[:10] or None



def safe_read_csv(path: Path) -> pd.DataFrame:
    """CSV loader that never crashes on ragged rows."""
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    except pd.errors.ParserError:
        return pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            engine="python",
            on_bad_lines="skip",
        )

def build_meta(chunk: str, fname: str, rd: RawDocument, idx: int) -> dict:
    eff = first_iso_date(
    rd.content,
    last_modified_fallback=rd.metadata.get("last_modified", "")
    )

    return {
        "doc_type":          rd.metadata.get("doc_type"),
        "jurisdiction_path": rd.metadata.get("jurisdiction_path"),
        "urls":              rd.metadata.get("urls"),
        "domains":           rd.metadata.get("domains"),
        "ner_entities":      rd.metadata.get("ner_entities"),
        "effective_date":    eff,
        "ingested_at":       now_iso(),
        "version_hash":      _sha(chunk),
        "expires_on":        None,
        "raw_id":            rd.id,
        "chunk_index":       idx,
    }

def chunk_and_save(*, advisor: str, country: str, force: bool = False) -> None:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    created = 0

    docs = (
        RawDocument.objects
        .filter(advisor__slug=advisor, country__name__iexact=country)
        .select_related("advisor", "country")
    )

    for rd in docs.iterator(chunk_size=500):
        h_cur  = rd.metadata.get("file_hash")
        h_prev = rd.metadata.get("chunked_file_hash")
        if not force and h_prev == h_cur:
            log.info("↩️  Skipping unchanged: %s", rd.source_path)
            continue

        log.info("✂️  Chunking %s", rd.source_path)
        with transaction.atomic():
            DocumentChunk.objects.filter(raw_document=rd).delete()

            ext = Path(rd.source_path).suffix.lower()
            ext = {".xllsx": ".xlsx", ".xlls": ".xls", ".xlsxx": ".xlsx", ".xll": ".xls"}.get(ext, ext)

            idx = 0
            # ── spreadsheet ──────────────────────────────────────────
            if ext in {".csv", ".xls", ".xlsx"}:
                fp = Path(settings.BASE_DIR) / "documents" / rd.source_path
                if not fp.exists():
                    log.error("File not found: %s", fp)
                    continue
                df = safe_read_csv(fp) if ext == ".csv" else pd.read_excel(fp, dtype=str, keep_default_na=False)
                for i, row in df.iterrows():
                    text = "\n".join(f"{c}: {row[c]}" for c in df.columns if row[c])
                    meta = build_meta(text, rd.filename, rd, i) | {"raw_id": rd.id, "chunk_index": i, "row_index": i}
                    DocumentChunk.objects.create(raw_document=rd, chunk_index=i, text=text, metadata=meta)
                    created += 1
                log.info("   ✅ %d rows", len(df))

            # ── text / PDF / HTML (content already extracted) ───────
            else:
                content = rd.content or ""
                caps    = re.split(r"\n([A-Z][A-Z\d\s\(\)\.\-]{4,})\n", content)
                sections = [caps[0]] + [f"{caps[i]}\n{caps[i+1]}" for i in range(1, len(caps), 2)] if len(caps) > 1 else [content]
                for sec in sections:
                    for chunk in splitter.split_text(sec):
                        meta = build_meta(chunk, rd.filename, rd, idx) | {"raw_id": rd.id, "chunk_index": idx}
                        DocumentChunk.objects.create(raw_document=rd, chunk_index=idx, text=chunk, metadata=meta)
                        idx += 1
                        created += 1
                log.info("   ✅ %d text chunks", idx)

            rd.metadata["chunked_file_hash"] = h_cur
            rd.save(update_fields=["metadata"])

    log.info("🎉 Done. %d new chunks", created)

# ── CLI helper for quick local runs (inside container) ─────────
if __name__ == "__main__":                                   # pragma: no cover
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("advisor")
    p.add_argument("country")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    chunk_and_save(advisor=args.advisor, country=args.country, force=args.force)
