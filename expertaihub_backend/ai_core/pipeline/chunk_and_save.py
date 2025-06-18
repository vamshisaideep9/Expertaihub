#!/usr/bin/env python
# ai_core/pipeline/chunk_and_save.py

import os
import sys
import django
import re
import logging
from datetime import datetime
from pathlib import Path
from django.db import transaction
from dateparser.search import search_dates

# ─── Django bootstrap ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
django.setup()
# ────────────────────────────────────────────────────────────────────────────

from django.conf import settings
from ai_core.models import RawDocument, DocumentChunk
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd

# ─── CONFIG ────────────────────────────────────────────────────────────────
CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 200
# ────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("chunk_and_save")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

# Date/jurisdiction patterns omitted for brevity; reuse yours:
MONTH_NAME      = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_PATTERNS   = [re.compile(r"\b" + MONTH_NAME + r" \d{1,2}, \d{4}\b")]
DATE_REGEX_TEXT = re.compile(r"(?:Effective|Eff\.)[:]?[ \t]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")
JURIS_PATTERNS  = [r"\b\d+\s*U\.S\.C\.?\s*§+\s*[\w\(\)\.\-]+"]


def parse_date_from_filename(filename: str) -> str | None:
    m = re.search(r"(\d{4})[-_](\d{2})[-_](\d{2})", filename)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{mo}-{d}"
    return None

def extract_dates_from_text(text: str) -> str | None:
    try:
        results = search_dates(text, settings={
            "PREFER_DAY_OF_MONTH": "first",
            "STRICT_PARSING": True
        }) or []
        dates = sorted({dt.date() for _, dt in results})
        if dates:
            return dates[0].isoformat()
    except Exception:
        pass
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m:
        mo, d, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None

def extract_jurisdictions(text: str) -> list[str]:
    cites = set()
    for pat in JURIS_PATTERNS:
        for match in re.findall(pat, text, flags=re.IGNORECASE):
            cites.add(match.strip())
    return sorted(cites)

def extract_metadata_free(text: str, filename: str, rd: RawDocument) -> dict:
    # 1) try filename → last_modified → header/footer/body
    eff_date = parse_date_from_filename(filename)
    if not eff_date:
        lm = rd.metadata.get("last_modified")
        if lm:
            eff_date = lm[:10]
    if not eff_date:
        eff_date = extract_dates_from_text("\n".join(text.splitlines()[:3]))
    if not eff_date:
        eff_date = extract_dates_from_text("\n".join(text.splitlines()[-3:]))
    if not eff_date:
        eff_date = extract_dates_from_text(text)

    jurisdictions = extract_jurisdictions(text)
    advisor = rd.advisor
    country = rd.country

    return {
        "effective_date":  eff_date,
        "jurisdiction":    jurisdictions,
        "advisor_slug":    getattr(advisor, 'slug', None) if advisor else None,
        "advisor_id":      getattr(advisor, 'id', None) if advisor else None,
        "country_name":    getattr(country, 'name', None) if country else None,
        "country_id":      getattr(country, 'id', None) if country else None,
    }


def chunk_and_save():
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )

    total_new_chunks = 0

    for rd in RawDocument.objects.select_related("advisor", "country").all():
        cur_hash  = rd.metadata.get("file_hash")
        prev_hash = rd.metadata.get("chunked_file_hash")
        if prev_hash == cur_hash:
            logger.info(f"↩️  Skipping unchanged: {rd.source_path}")
            continue

        logger.info(f"✂️  Chunking document: {rd.source_path}")
        with transaction.atomic():
            DocumentChunk.objects.filter(raw_document=rd).delete()

            ext = Path(rd.source_path).suffix.lower()
            # Handle common typos in Excel file extensions
            if ext in {".xllsx", ".xlls", ".xlsxx"}:
                ext = ".xlsx"
            elif ext in {".xll", ".xlsxx"}:
                ext = ".xls"
            idx = 0

            # ─── Spreadsheet: one chunk per row ───────────────────────────────
            if ext in {".csv", ".xls", ".xlsx"}:
                try:
                    file_path = Path(settings.BASE_DIR) / "documents" / rd.source_path
                    if not file_path.exists():
                        logger.error(f"❌ File not found: {file_path}")
                        continue
                        
                    df = (pd.read_csv(file_path) if ext == ".csv"
                          else pd.read_excel(file_path))
                    for i, row in df.iterrows():
                        # render the row as "col: val" lines
                        parts = [f"{col}: {row[col]}" for col in df.columns if pd.notnull(row[col])]
                        text = "\n".join(parts)
                        md   = extract_metadata_free(text, rd.filename, rd)
                        md.update({"raw_id": rd.id, "chunk_index": i, "row_index": i})
                        DocumentChunk.objects.create(
                            raw_document=rd,
                            chunk_index=i,
                            text=text,
                            metadata=md,
                        )
                        total_new_chunks += 1
                    logger.info(f"   ✅ Created {len(df)} row-chunks for {rd.source_path}")
                except FileNotFoundError:
                    logger.error(f"❌ File not found: {rd.source_path}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error processing spreadsheet {rd.source_path}: {e}")
                    continue

            # ─── Everything else: heading/text splitter ───────────────────────
            else:
                raw_text = rd.content or ""
                parts = re.split(r"\n([A-Z][A-Z\d\s\(\)\.-]{4,})\n", raw_text)
                sections = (
                    [parts[0]] + [f"{parts[i]}\n{parts[i+1]}" for i in range(1, len(parts), 2)]
                    if len(parts) > 1 else [raw_text]
                )
                logger.info(f"   ➗ Split into {len(sections)} sections")
                for sec in sections:
                    for chunk_text in splitter.split_text(sec):
                        md = extract_metadata_free(chunk_text, rd.filename, rd)
                        md.update({"raw_id": rd.id, "chunk_index": idx})
                        DocumentChunk.objects.create(
                            raw_document=rd,
                            chunk_index=idx,
                            text=chunk_text,
                            metadata=md,
                        )
                        idx += 1
                        total_new_chunks += 1
                logger.info(f"   ✅ Created {idx} text-chunks for {rd.source_path}")

            # mark chunked
            rd.metadata["chunked_file_hash"] = cur_hash
            rd.save(update_fields=["metadata"])

    logger.info(f"🎉 chunk_and_save complete: {total_new_chunks} new chunks created")


if __name__ == "__main__":
    chunk_and_save()
