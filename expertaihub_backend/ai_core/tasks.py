# ai_core/tasks.py

from celery import shared_task
from django.conf import settings
import os, requests
import time
import calendar
from datetime import date
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables from .env
load_dotenv()

@shared_task
def fetch_uscode_title8_pdf():
    """
    Download US Code Title 8 PDF via GovInfo’s API endpoint,
    using API key from .env, and save to:
      <project_root>/documents/immigration/usa/uscode/<YYYY_MM>/USCODE-2023-title8.pdf
    """
    # 1) Build target path
    today   = date.today()
    stamp   = f"{today.year}_{today.month:02d}"
    base    = settings.DOCS_DIR
    target  = os.path.join(base, "uscode", stamp)
    os.makedirs(target, exist_ok=True)

    # 2) Get API key and download
    api_key = os.getenv("GOVINFO_KEY")
    if not api_key:
        raise RuntimeError("GOVINFO_KEY not set in .env")
    url     = f"https://api.govinfo.gov/packages/USCODE-2023-title8/pdf?api_key={api_key}"
    r       = requests.get(url, stream=True)
    r.raise_for_status()
    if "pdf" not in r.headers.get("Content-Type", "").lower():
        raise RuntimeError(f"Expected PDF but got {r.headers.get('Content-Type')}")

    # 3) Write to disk
    out_path = os.path.join(target, "USCODE-2023-title8.pdf")
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)

    return f"Saved USCODE-2023-title8.pdf to {out_path}"


@shared_task
def fetch_cfr_title8_vol1_pdf():
    """
    Download CFR Title 8 Vol 1 PDF via GovInfo’s API endpoint,
    using API key from .env, and save to:
      <project_root>/documents/immigration/usa/cfr/<YYYY_MM>/CFR-2023-title8-vol1.pdf
    """
    # 1) Build target path
    today   = date.today()
    stamp   = f"{today.year}_{today.month:02d}"
    base    = settings.DOCS_DIR
    target  = os.path.join(base, "cfr", stamp)
    os.makedirs(target, exist_ok=True)

    # 2) Get API key and download
    api_key = os.getenv("GOVINFO_KEY")
    if not api_key:
        raise RuntimeError("GOVINFO_KEY not set in .env")
    url     = f"https://api.govinfo.gov/packages/CFR-2023-title8-vol1/pdf?api_key={api_key}"
    r       = requests.get(url, stream=True)
    r.raise_for_status()
    if "pdf" not in r.headers.get("Content-Type", "").lower():
        raise RuntimeError(f"Expected PDF but got {r.headers.get('Content-Type')}")

    # 3) Write to disk
    out_path = os.path.join(target, "CFR-2023-title8-vol1.pdf")
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)

    return f"Saved CFR-2023-title8-vol1.pdf to {out_path}"



@shared_task
def fetch_federal_register_notices():
    """
    Download all Federal Register “NOTICE” documents from the prior month:
      1) Query the API for NOTICE docs published between first-of-last-month and first-of-this-month.
      2) Save the JSON index and download each PDF into:
         <project_root>/documents/immigration/usa/federal_register/<YYYY_MM>/
    """
    from datetime import date

    today = date.today()
    # first of this month
    first_this = today.replace(day=1)
    # compute last month
    if first_this.month == 1:
        prev_year, prev_month = first_this.year - 1, 12
    else:
        prev_year, prev_month = first_this.year, first_this.month - 1

    start = date(prev_year, prev_month, 1).isoformat()
    end   = first_this.isoformat()

    # build target dir
    stamp = f"{prev_year}_{prev_month:02d}"
    base  = settings.DOCS_DIR
    target = os.path.join(base, "federal_register", stamp)
    os.makedirs(target, exist_ok=True)

    # 1) fetch JSON index
    api_url = "https://www.federalregister.gov/api/v1/documents"
    params = {
        "conditions[publication_date][gte]": start,
        "conditions[publication_date][lt]": end,
        "conditions[type]": "NOTICE",
        "per_page": 100,
        "order": "publication_date"
    }
    resp = requests.get(api_url, params=params)
    resp.raise_for_status()
    results = resp.json().get("results", [])

    # save index
    idx_path = os.path.join(target, "notices_index.json")
    with open(idx_path, "w", encoding="utf-8") as jf:
        jf.write(resp.text)

    # 2) download each PDF
    count = 0
    for doc in results:
        pdf = doc.get("pdf_url")
        if not pdf:
            continue
        fn = os.path.basename(pdf)
        out = os.path.join(target, fn)
        if os.path.exists(out):
            continue
        p = requests.get(pdf, stream=True)
        p.raise_for_status()
        with open(out, "wb") as pf:
            for chunk in p.iter_content(8192):
                if chunk:
                    pf.write(chunk)
        count += 1

    return f"Fetched {len(results)} notices ({count} PDFs) to {target}"




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




@shared_task
def fetch_uscis_policy_manual():
    """
    Scrape the USCIS Policy Manual page for all chapter PDFs,
    download any new ones into:
      documents/immigration/usa/uscis_policy_manual/<YYYY_MM>/
    """
    from bs4 import BeautifulSoup
    from datetime import date
    import os, requests    
    today   = date.today()
    stamp   = f"{today.year}_{today.month:02d}"
    base    = settings.DOCS_DIR
    target  = os.path.join(base, "uscis_policy_manual", stamp)
    os.makedirs(target, exist_ok=True)

    # 1️⃣ fetch the landing page
    url  = "https://www.uscis.gov/policy-manual"
    resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 2️⃣ find all .pdf links
    count = 0
    for a in soup.select("a[href$='.pdf']"):
        href = a["href"]
        pdf_url = href if href.startswith("http") else f"https://www.uscis.gov{href}"
        fn = os.path.basename(pdf_url)
        out = os.path.join(target, fn)
        if os.path.exists(out):
            continue
        # 3️⃣ download
        dl = requests.get(pdf_url, stream=True)
        dl.raise_for_status()
        with open(out, "wb") as f:
            for chunk in dl.iter_content(8192):
                if chunk:
                    f.write(chunk)
        count += 1

    return f"Downloaded {count} USCIS Policy Manual PDFs to {target}"




import os
import requests
from celery import shared_task
from django.conf import settings
from bs4 import BeautifulSoup

@shared_task
def fetch_bia_precedent_volumes():
    """
    Download all EOIR Precedent Decisions PDFs from Volumes 08–29.
    Each volume page at:
      https://www.justice.gov/eoir/precedent-decisions-volume-XX
    is scraped for *.pdf links and saved to:
      <project>/documents/immigration/usa/bia_precedent_volumes/volume-XX/
    """
    base_dir = settings.DOCS_DIR
    target_root = os.path.join(base_dir, "bia_precedent_volumes")
    os.makedirs(target_root, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    downloaded = 0

    for vol in range(2, 22):  # 8 through 29 inclusive
        vol_str = f"{vol}"
        url = f"https://www.justice.gov/eoir/listing-volume-{vol_str}-decisions"
        resp = session.get(url)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        # find all PDF anchors
        pdf_links = {
            a["href"] if a["href"].startswith("http")
            else f"https://www.justice.gov{a['href']}"
            for a in soup.select("a[href$='.pdf']")
        }

        # prepare volume folder
        vol_folder = os.path.join(target_root, f"listing-volume-{vol_str}")
        os.makedirs(vol_folder, exist_ok=True)

        for pdf_url in sorted(pdf_links):
            fn = os.path.basename(pdf_url.split("?",1)[0])
            out_path = os.path.join(vol_folder, fn)
            if os.path.exists(out_path):
                continue
            dl = session.get(pdf_url, stream=True)
            dl.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in dl.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            downloaded += 1

    return f"Downloaded {downloaded} precedent PDFs across Volumes 08–29"



@shared_task
def fetch_immigration_law_advisor_pdfs():
    """
    Scrape https://www.justice.gov/eoir/immigration-law-advisor for all PDF links
    and download them into:
      <project_root>/documents/immigration/usa/immigration_law_advisor/<YYYY_MM>/
    """
    # 1) Prepare output directory
    today  = date.today()
    stamp  = f"{today.year}_{today.month:02d}"
    base   = settings.DOCS_DIR
    target = os.path.join(base, "immigration_law_advisor", stamp)
    os.makedirs(target, exist_ok=True)

    # 2) Fetch the Immigration Law Advisor page
    url     = "https://www.justice.gov/eoir/immigration-law-advisor"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp    = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup    = BeautifulSoup(resp.text, "html.parser")

    # 3) Collect all PDF URLs
    pdf_urls = set()
    for a in soup.select("a[href$='.pdf']"):
        href = a["href"]
        if href.startswith("http"):
            pdf_urls.add(href)
        else:
            pdf_urls.add("https://www.justice.gov" + href)

    # 4) Download each PDF
    downloaded = 0
    for pdf_url in sorted(pdf_urls):
        filename = os.path.basename(pdf_url.split("?", 1)[0])
        out_path = os.path.join(target, filename)
        if os.path.exists(out_path):
            continue

        dl = requests.get(pdf_url, headers=headers, stream=True)
        dl.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in dl.iter_content(8192):
                if chunk:
                    f.write(chunk)
        downloaded += 1

    return f"Downloaded {downloaded} Immigration Law Advisor PDFs into {target}"


# ai_core/tasks.py


import pdfkit
import json
import logging


logger = logging.getLogger(__name__)

@shared_task
def fetch_immigration_impact_texts(year: int = None, month: int = None, day: int = None):
    """
    Fetch Immigration Impact articles for a given date (or today if none passed).
    Args (all optional):
      year, month, day  – integers for the archive URL.
    Extracts all <h1>–<h6> and <p> under .post-content.entry-content
    and writes JSON to:
      documents/immigration/usa/immigration_impact/YYYY_MM_DD/<slug>/article.json
    """
    # 1️⃣ Determine which date to use
    if year and month and day:
        d = date(year, month, day)
    else:
        d = date.today()

    stamp = f"{d.year}_{d.month:02d}_{d.day:02d}"
    base  = settings.DOCS_DIR
    archive_url = f"https://immigrationimpact.com/{d.year}/{d.month:02d}/{d.day:02d}/"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(archive_url, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.info(f"No archive for {stamp}, skipping")
        return f"No archive for {stamp}"
    except Exception as e:
        logger.error(f"Error fetching archive {archive_url}: {e}")
        return f"Error fetching archive for {stamp}"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Tighten selector to just the article previews
    article_links = {
        (a["href"] if a["href"].startswith("http")
         else "https://immigrationimpact.com" + a["href"])
        for a in soup.select("h2.post-title a[href]")
    }

    if not article_links:
        logger.info(f"No articles found on {archive_url}")
        return f"No articles for {stamp}"

    processed = 0
    for link in sorted(article_links):
        slug = link.rstrip("/").split("/")[-1]
        out_dir = os.path.join(base, "immigration_impact", stamp, slug)
        os.makedirs(out_dir, exist_ok=True)

        try:
            art = requests.get(link, headers=headers, timeout=30)
            art.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch {link}: {e}")
            continue

        page = BeautifulSoup(art.text, "html.parser")
        content = page.select_one("article .post-content.entry-content")
        if not content:
            logger.warning(f"No content at {link}")
            continue

        elements = []
        for el in content.find_all(["h1","h2","h3","h4","h5","h6","p"]):
            text = el.get_text(strip=True)
            if text:
                elements.append({"tag": el.name, "text": text})

        json_path = os.path.join(out_dir, "article.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump({
                "url": link,
                "fetched_on": d.isoformat(),
                "elements": elements
            }, jf, ensure_ascii=False, indent=2)

        processed += 1

    return f"Saved text for {processed} articles on {stamp}"





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


@shared_task
def fetch_ca9_immigration_outline_pdfs():
    """
    Scrape https://www.ca9.uscourts.gov/guides/immigration-outline/ for PDF links
    and download each into:
      <PROJECT_ROOT>/documents/immigration/usa/federal_court_guides/ca9_immigration_outline/<YYYY_MM>/
    """
    # 1) Prepare output directory
    today     = date.today()
    stamp     = f"{today.year}_{today.month:02d}"
    base      = settings.DOCS_DIR
    target    = os.path.join(base, "federal_court_guides", "ca9_immigration_outline", stamp)
    os.makedirs(target, exist_ok=True)

    # 2) Fetch the outline page
    url     = "https://www.ca9.uscourts.gov/guides/immigration-outline/"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp    = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 3) Collect all PDF URLs
    pdf_urls = set()
    for a in soup.select("a[href$='.pdf']"):
        href = a["href"]
        if href.startswith("http"):
            pdf_urls.add(href)
        else:
            # relative path on ca9 site
            pdf_urls.add(requests.compat.urljoin(url, href))

    # 4) Download each PDF
    downloaded = 0
    for pdf_url in sorted(pdf_urls):
        filename = os.path.basename(pdf_url.split("?", 1)[0])
        out_path = os.path.join(target, filename)
        if os.path.exists(out_path):
            continue
        try:
            dl = requests.get(pdf_url, headers=headers, stream=True, timeout=60)
            dl.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in dl.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            downloaded += 1
        except Exception as e:
            # Optionally log with logger.error(...)
            print(f"Failed to download {pdf_url}: {e}")

    return f"Downloaded {downloaded} CA9 Immigration Outline PDFs into {target}"



@shared_task
def fetch_dhs_admin_management_pdfs():
    """
    Scrape https://www.dhs.gov/publication/administrative-management
    for all PDF links and download each into:
      <PROJECT_ROOT>/documents/immigration/usa/administrative_management/<YYYY_MM>/
    """
    # 1) Prepare output directory
    today = date.today()
    stamp = f"{today.year}_{today.month:02d}"
    base = settings.DOCS_DIR
    target = os.path.join(
        base,
        "immigration",
        "usa",
        "administrative_management",
        stamp
    )
    os.makedirs(target, exist_ok=True)

    # 2) Fetch the Administrative Management page
    index_url = "https://www.dhs.gov/publication/workforce-management"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(index_url, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 3) Find all PDF links on the page
    pdf_urls = set()
    for a in soup.select("a[href$='.pdf']"):
        href = a["href"]
        # Some links may be protocol‐relative or relative
        pdf_urls.add(requests.compat.urljoin(index_url, href))

    downloaded = 0

    # 4) Download each PDF
    for pdf_url in sorted(pdf_urls):
        filename = os.path.basename(pdf_url.split("?", 1)[0])
        out_path = os.path.join(target, filename)
        if os.path.exists(out_path):
            continue

        try:
            dl = requests.get(pdf_url, headers=headers, stream=True, timeout=60)
            dl.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in dl.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            downloaded += 1
        except Exception as e:
            # Optionally log the failure:
            print(f"Failed to download {pdf_url}: {e}")

    return f"Downloaded {downloaded} Administrative Management PDFs into {target}"



@shared_task(bind=True)
def download_ice_nds2000_pdfs(self, base_url="https://www.ice.gov/foia/library", output_dir=None):
    """
    Scrape the ICE 2000 Detention Standards page for PDF links
    and download each into `output_dir`.
    """
    output_dir = output_dir or os.path.join(os.getcwd(), "ice_nds2000_pdfs")
    os.makedirs(output_dir, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    })

    logger.info(f"Fetching ICE 2000‐standards page: {base_url}")
    resp = session.get(base_url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    pdf_links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().endswith(".pdf"):
            pdf_links.add(requests.compat.urljoin(base_url, href))

    logger.info(f"Found {len(pdf_links)} unique PDF URLs")

    downloaded = 0
    for pdf_url in pdf_links:
        filename = os.path.basename(pdf_url.split("?")[0])
        target_path = os.path.join(output_dir, filename)

        if os.path.exists(target_path):
            logger.info(f"  → already have {filename}, skipping")
            continue

        logger.info(f"  → downloading {filename} from {pdf_url}")
        try:
            with session.get(pdf_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(target_path, "wb") as f:
                    for chunk in r.iter_content(32 * 1024):
                        if chunk:
                            f.write(chunk)
            logger.info(f"     saved to {target_path}")
            downloaded += 1
        except Exception as e:
            logger.error(f"     failed to download {pdf_url}: {e}")

        # update Celery state
        self.update_state(state="PROGRESS", meta={
            "downloaded": downloaded,
        })

    logger.info(f"Task complete: downloaded {downloaded} PDFs to {output_dir}")
    return {"downloaded": downloaded, "output_dir": output_dir}




