# ai_core/tasks.py

from celery import shared_task
from django.conf import settings
import os, requests
import time
import calendar
from datetime import date
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
import re

# Load environment variables from .env
load_dotenv()



# ai_core/tasks.py

from celery import shared_task
from django.conf import settings
from datetime import date
import calendar, os, requests
from openai import OpenAI

@shared_task
def fetch_visa_bulletin():
    """
    1) Build the URL for the current month’s Visa Bulletin.
    2) Download the PDF and save to:
       <project_root>/documents/immigration/usa/visa_bulletin/<YYYY_MM>/.
    """
    today   = date.today()
    stamp   = f"{today.year}_{today.month:02d}"
    base    = settings.DOCS_DIR
    target  = os.path.join(base, "visa_bulletin", stamp)
    os.makedirs(target, exist_ok=True)


    month_name = calendar.month_name[today.month].lower()  #
    url = (
        f"https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/"
        f"{today.year}/visa-bulletin-for-{month_name}-{today.year}.html"
    )

    # 3️⃣ Scrape the page for the PDF link
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")

    link = soup.find("a", href=lambda h: h and h.endswith(".pdf"))
    if not link:
        raise RuntimeError(f"No PDF found on {url}")
    href = link["href"]
    pdf_url = href if href.startswith("http") else f"https://travel.state.gov{href}"

    # 4️⃣ Download the PDF
    fn      = os.path.basename(pdf_url)
    outpath = os.path.join(target, fn)
    dl = requests.get(pdf_url, stream=True)
    dl.raise_for_status()
    if "pdf" not in dl.headers.get("Content-Type", "").lower():
        raise RuntimeError("Expected PDF content")
    with open(outpath, "wb") as f:
        for chunk in dl.iter_content(8192):
            if chunk:
                f.write(chunk)

    return f"Saved Visa Bulletin {fn} to {outpath}"


from datetime import datetime

@shared_task
def fetch_uscis_policy_manual():
    """
    1) Fetch https://www.uscis.gov/policy-manual
    2) Parse the "Current as of" date on the page
    3) If that date's PDF isn't already downloaded, find the PDF link
       and save it under:
         <DOCS_DIR>/uscis_policy_manual/<YYYY_MM_DD>/USCIS_Policy_Manual_<YYYY_MM_DD>.pdf
    """
    base_url = "https://www.uscis.gov/policy-manual"
    resp = requests.get(base_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # ── 1) Parse the "Current as of" line
    date_str = None
    
    # Try multiple selectors for the date
    selectors = [
        ".field--name-field-display-date .field__item time",
        ".field--name-field-display-date",
        ".field__item time",
        "time[datetime]",
        ".current-as-of"
    ]
    
    for selector in selectors:
        date_el = soup.select_one(selector)
        if date_el:
            # Try to get datetime attribute first (ISO 8601 format)
            date_str = date_el.get('datetime', '').strip()
            if not date_str:
                # Fall back to text content
                date_str = date_el.get_text(strip=True)
            if date_str:
                break
    
    # If no date found in structured elements, try text search
    if not date_str:
        # Look for text containing "Current as of" or similar phrases
        date_texts = [
            "Current as of",
            "Last Updated",
            "Updated",
            "Published"
        ]
        for text in date_texts:
            date_el = soup.find(text=lambda t: t and text in t)
            if date_el:
                # Extract the date part after the label
                parts = date_el.split(text, 1)
                if len(parts) > 1:
                    date_str = parts[1].strip()
                    break
    
    # If still no date found, try to find any date-like text
    if not date_str:
        # Look for text that matches common date patterns
        date_patterns = [
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, soup.get_text())
            if matches:
                date_str = matches[0]
                break

    if not date_str:
        # If we still can't find a date, use today's date as a fallback
        from datetime import date
        today = date.today()
        date_str = today.strftime("%B %d, %Y")
        print(f"Warning: Could not find date on page, using today's date: {date_str}")

    try:
        # Try different date formats
        date_formats = [
            "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 with Z timezone (2025-06-06T12:00:00Z)
            "%Y-%m-%dT%H:%M:%S%z", # ISO 8601 with timezone offset
            "%Y-%m-%dT%H:%M:%S",   # ISO 8601 without timezone
            "%Y-%m-%d",            # ISO date only
            "%B %d, %Y",           # June 6, 2025
            "%B %d %Y",            # June 6 2025
            "%b %d, %Y",           # Jun 6, 2025
            "%b %d %Y",            # Jun 6 2025
            "%m/%d/%Y",            # 06/06/2025
            "%d/%m/%Y"             # 06/06/2025
        ]
        
        dt = None
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
                
        if not dt:
            # If all formats fail, try parsing just the date part from ISO format
            if 'T' in date_str:
                try:
                    date_only = date_str.split('T')[0]
                    dt = datetime.strptime(date_only, "%Y-%m-%d")
                except ValueError:
                    pass
                    
        if not dt:
            raise ValueError(f"Could not parse date string: {date_str}")
            
        stamp = dt.strftime("%Y_%m_%d")
    except Exception as e:
        raise RuntimeError(f"Failed to parse date '{date_str}': {e}")

    # ── 2) Skip if already have this version
    target_dir = os.path.join(settings.DOCS_DIR, "uscis_policy_manual", stamp)
    if os.path.exists(target_dir):
        return f"No new update (already have {stamp})"
    os.makedirs(target_dir, exist_ok=True)

    # ── 3) Locate the PDF link on the page
    # Try multiple methods to find the PDF link
    pdf_link = None
    
    # Method 1: Direct PDF links
    pdf_link = soup.find("a", href=lambda h: h and h.lower().endswith(".pdf"))
    
    # Method 2: Links containing specific text
    if not pdf_link:
        pdf_link = soup.find("a", text=lambda t: t and any(x in t for x in ["Policy Manual", "PDF", "Download"]))
    
    # Method 3: Links in specific sections
    if not pdf_link:
        for section in soup.find_all(["div", "section"], class_=lambda c: c and any(x in str(c).lower() for x in ["download", "pdf", "manual"])):
            pdf_link = section.find("a", href=True)
            if pdf_link:
                break
    
    if not pdf_link:
        raise RuntimeError("No PDF download link found on USCIS page")
    
    pdf_href = pdf_link["href"]
    pdf_url = pdf_href if pdf_href.startswith("http") else urljoin(base_url, pdf_href)

    # ── 4) Download and save
    filename = f"USCIS_Policy_Manual_{stamp}.pdf"
    outpath = os.path.join(target_dir, filename)

    try:
        dl = requests.get(pdf_url, headers={"User-Agent":"Mozilla/5.0"}, stream=True, timeout=60)
        dl.raise_for_status()
        if "pdf" not in dl.headers.get("Content-Type", "").lower():
            raise RuntimeError(f"Expected PDF, got {dl.headers.get('Content-Type')}")

        with open(outpath, "wb") as f:
            for chunk in dl.iter_content(8192):
                if chunk:
                    f.write(chunk)

        return f"Downloaded USCIS Policy Manual ({stamp}) to {outpath}"
    except Exception as e:
        raise RuntimeError(f"Failed to download PDF: {e}")





@shared_task
def fetch_uscis_policy_memos():
    """
    Scrape USCIS Policy Memoranda (2019–present) across pages 0–16,
    and download each PDF into:
      <DOCS_DIR>/uscis_policy_manual/<YEAR>/
    """
    base_listing = "https://www.uscis.gov/laws-and-policy/policy-memoranda"
    today        = date.today()
    base_dir     = settings.DOCS_DIR
    total        = 0

    # iterate pages 0 (first) through 16
    for page in range(17):
        page_url = base_listing if page == 0 else f"{base_listing}?page={page}"
        resp     = requests.get(page_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try table-based listing first
        rows = (
            soup.select("table.views-table tbody tr")
            or soup.select(".views-row")
        )

        for row in rows:
            # 1) extract the publication date text to get the year
            date_cell = row.select_one(".views-field-field-publication-date")
            if date_cell:
                # e.g. "Jan. 5, 2019" → "2019"
                year = date_cell.get_text(strip=True)[-4:]
            else:
                year = str(today.year)

            # 2) find all PDF links in that row
            for a in row.select("a[href$='.pdf']"):
                href    = a["href"]
                pdf_url = href if href.startswith("http") else urljoin(base_listing, href)
                filename = os.path.basename(pdf_url.split("?", 1)[0])

                # 3) build per-year folder
                target = os.path.join(base_dir, "uscis_policy_memos", year)
                os.makedirs(target, exist_ok=True)
                outpth = os.path.join(target, filename)

                # skip if already downloaded
                if os.path.exists(outpth):
                    continue

                # 4) download & save
                dl = requests.get(pdf_url, headers={"User-Agent":"Mozilla/5.0"}, stream=True, timeout=60)
                dl.raise_for_status()
                with open(outpth, "wb") as f:
                    for chunk in dl.iter_content(8192):
                        if chunk:
                            f.write(chunk)

                total += 1

    return f"Downloaded {total} Policy Manual PDFs into {os.path.join(base_dir, 'uscis_policy_manual')}"




# ai_core/tasks.py

import os
import requests
from celery import shared_task
from django.conf import settings
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

@shared_task
def fetch_all_uscis_form_pdfs():
    """
    1) Scrape the USCIS All Forms page for each form-detail link.
    2) Visit each form page, locate the "Forms and Document Downloads" section,
       collect all PDF URLs there.
    3) Download every PDF into:
         <DOCS_DIR>/forms/<form_slug>/
    where `form_slug` is taken from the form-detail URL path.
    """
    base_listing = "https://www.uscis.gov/forms/all-forms"
    headers      = {"User-Agent": "Mozilla/5.0"}
    session      = requests.Session()
    session.headers.update(headers)

    # 1️⃣ fetch the listing page
    resp = session.get(base_listing, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 2️⃣ find each form-detail link
    form_links = []
    for a in soup.select("a.link--form-title"):
        href = a.get("href")
        if not href:
            continue
        full_url = href if href.startswith("http") else urljoin(base_listing, href)
        form_links.append(full_url)
    form_links = sorted(set(form_links))

    downloaded = 0

    for form_url in form_links:
        # derive a slug from the URL path, e.g. "/forms/i-90" → "i-90"
        path = urlparse(form_url).path.rstrip("/")
        form_slug = path.split("/")[-1]

        # prepare target directory
        target_dir = os.path.join(settings.DOCS_DIR, "forms", form_slug)
        os.makedirs(target_dir, exist_ok=True)

        # 3️⃣ fetch the form-detail page
        r2 = session.get(form_url, timeout=30)
        r2.raise_for_status()
        page_soup = BeautifulSoup(r2.text, "html.parser")

        # 4️⃣ locate the "Forms and Document Downloads" section
        section = None
        for header in page_soup.select("h2, h3"):
            if header.get_text(strip=True).lower() == "forms and document downloads":
                # the section is everything after this header until the next header of same level
                section = header.find_next_sibling()
                break

        if not section:
            # fallback: search the entire page for PDF links
            pdf_anchors = page_soup.select("a[href$='.pdf']")
        else:
            # collect only within this section
            pdf_anchors = section.find_all("a", href=lambda h: h and h.lower().endswith(".pdf"))

        # 5️⃣ download each PDF
        for a in pdf_anchors:
            href = a["href"]
            pdf_url = href if href.startswith("http") else urljoin(form_url, href)
            fn = os.path.basename(pdf_url.split("?", 1)[0])
            out = os.path.join(target_dir, fn)
            if os.path.exists(out):
                continue
            try:
                dl = session.get(pdf_url, stream=True, timeout=60)
                dl.raise_for_status()
                with open(out, "wb") as f:
                    for chunk in dl.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                downloaded += 1
            except Exception:
                # skip failures silently
                continue

    return f"Downloaded {downloaded} USCIS form PDFs into {os.path.join(settings.DOCS_DIR, 'forms')}"


# ai_core/tasks.py

import os
import json
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from celery import shared_task
from django.conf import settings
from bs4 import BeautifulSoup

# where we store JSON outputs and state
STATE_DIR   = os.path.join(settings.DOCS_DIR, "newsroom")
STATE_FILE  = os.path.join(STATE_DIR, "fetched_urls.json")
LISTING_URL = "https://www.uscis.gov/newsroom/news-releases"

@shared_task
def fetch_uscis_news_releases():
    """
    1) On first-ever run (empty state), scrape pages 0–9 of the USCIS News Releases listing
       (LISTING_URL?page=0 through ?page=9) to get all past URLs.
    2) On subsequent runs, scrape only page=0 to detect new releases.
    3) For each URL not yet seen:
         • scrape its <h1> + all <p> under <article>
         • save as JSON under STATE_DIR/YYYY_MM_DD/<slug>.json
         • record it in STATE_FILE
    """
    # ── 0) load or initialize state
    os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {"fetched_urls": []}

    # ── 1) decide which pages to scrape
    if not state["fetched_urls"]:
        pages = range(0, 10)      # seed run: pages 0–9
    else:
        pages = [0]               # subsequent runs: only latest page

    # ── 2) collect candidate URLs
    candidate_urls = []
    for page in pages:
        page_url = LISTING_URL if page == 0 else f"{LISTING_URL}?page={page}"
        r = requests.get(page_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href*='/newsroom/news-releases/']"):
            href = a["href"]
            full = href if href.startswith("http") else urljoin(LISTING_URL, href)
            candidate_urls.append(full)
    # dedupe while preserving order
    candidate_urls = list(dict.fromkeys(candidate_urls))

    # ── 3) filter to new URLs
    new_urls = [u for u in candidate_urls if u not in state["fetched_urls"]]
    if not new_urls:
        return "No new USCIS news releases found."

    # ── 4) scrape & save each new release
    fetched = []
    for url in new_urls:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # title & paragraphs
        title   = (soup.find("h1") or soup).get_text(strip=True)
        article = soup.find("article") or soup
        paras   = [p.get_text(strip=True) for p in article.find_all("p")]

        # slug + timestamp
        slug  = urlparse(url).path.rstrip("/").split("/")[-1]
        stamp = datetime.utcnow().strftime("%Y_%m_%d")

        out_dir  = os.path.join(STATE_DIR, stamp)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{slug}.json")

        with open(out_path, "w", encoding="utf-8") as jf:
            json.dump({
                "url": url,
                "fetched_on": datetime.utcnow().isoformat(),
                "title": title,
                "paragraphs": paras
            }, jf, ensure_ascii=False, indent=2)

        state["fetched_urls"].append(url)
        fetched.append(url)

    # ── 5) persist updated state
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return f"Fetched {len(fetched)} new releases: {fetched}"




# where we store JSON outputs and state for alerts
ALERTS_DIR   = os.path.join(settings.DOCS_DIR, "alerts")
ALERTS_STATE = os.path.join(ALERTS_DIR, "fetched_alert_urls.json")
ALERTS_LIST  = "https://www.uscis.gov/newsroom/alerts"

@shared_task
def fetch_uscis_alerts():
    """
    1) On first run (empty state), scrape pages 0–19 of the USCIS Alerts listing
       (ALERTS_LIST?page=0 through ?page=19) to seed all past URLs.
    2) On subsequent runs, scrape only page=0 to detect new alerts.
    3) For each URL not yet seen:
         • scrape its <h1> + all <p> under <article>
         • save as JSON under ALERTS_DIR/YYYY_MM_DD/<slug>.json
         • record it in ALERTS_STATE
    """
    # ── load or init state
    os.makedirs(ALERTS_DIR, exist_ok=True)
    if os.path.exists(ALERTS_STATE):
        with open(ALERTS_STATE, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {"fetched_urls": []}

    # ── choose pages to scrape
    pages = range(0, 20) if not state["fetched_urls"] else [0]

    # ── collect candidate URLs
    candidates = []
    for page in pages:
        url = ALERTS_LIST if page == 0 else f"{ALERTS_LIST}?page={page}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href*='/newsroom/alerts/']"):
            href = a["href"]
            full = href if href.startswith("http") else urljoin(ALERTS_LIST, href)
            candidates.append(full)
    # dedupe
    candidates = list(dict.fromkeys(candidates))

    # ── filter new
    new_urls = [u for u in candidates if u not in state["fetched_urls"]]
    if not new_urls:
        return "No new USCIS alerts found."

    fetched = []
    for alert_url in new_urls:
        resp = requests.get(alert_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # title and body
        title_el = soup.find("h1")
        title    = title_el.get_text(strip=True) if title_el else "No Title"
        article  = soup.find("article") or soup
        paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]

        # derive slug and date
        slug  = urlparse(alert_url).path.rstrip("/").split("/")[-1]
        stamp = datetime.utcnow().strftime("%Y_%m_%d")

        out_dir  = os.path.join(ALERTS_DIR, stamp)
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f"{slug}.json")

        with open(out_file, "w", encoding="utf-8") as jf:
            json.dump({
                "url": alert_url,
                "fetched_on": datetime.utcnow().isoformat(),
                "title": title,
                "paragraphs": paragraphs
            }, jf, ensure_ascii=False, indent=2)

        state["fetched_urls"].append(alert_url)
        fetched.append(alert_url)

    # ── persist state
    with open(ALERTS_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return f"Fetched {len(fetched)} new alerts: {fetched}"