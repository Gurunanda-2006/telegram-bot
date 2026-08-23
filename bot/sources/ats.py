import hashlib
import logging
from datetime import datetime, timezone

import requests

log = logging.getLogger(__name__)

TIMEOUT = 15
HEADERS = {"User-Agent": "placement-digest-bot/1.0"}


def _make_id(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _mk(company, title, url, location="", employment="", published=""):
    return {
        "id": _make_id(url),
        "source": "ats",
        "company": company,
        "title": (title or "").strip(),
        "url": url,
        "location": location or "",
        "employment": employment or "",
        "published": published,
        "extra_text": "",
    }


def fetch_all_ats(companies_cfg):
    items = []
    for entry in companies_cfg.get("companies", []):
        platform = entry.get("ats")
        if not platform:
            continue
        fn = PLATFORMS.get(platform)
        if not fn:
            log.warning("unknown platform %r for %s", platform, entry["name"])
            continue
        try:
            postings = fn(entry["name"], entry["board"])
            items.extend(postings)
            log.info("%s (%s): %d postings", entry["name"], platform, len(postings))
        except Exception as exc:
            log.warning("ATS fetch failed for %s: %s", entry["name"], exc)
    return items


def _greenhouse(company, board):
    resp = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    out = []
    for job in resp.json().get("jobs", []):
        out.append(
            _mk(
                company,
                job.get("title"),
                job.get("absolute_url") or "",
                (job.get("location") or {}).get("name") or "",
                published=job.get("updated_at") or "",
            )
        )
    return out


def _lever(company, board):
    resp = requests.get(
        f"https://api.lever.co/v0/postings/{board}?mode=json",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    out = []
    for job in resp.json():
        cats = job.get("categories") or {}
        created = int(job.get("createdAt") or 0)
        published = (
            datetime.fromtimestamp(created / 1000, tz=timezone.utc).date().isoformat()
            if created
            else ""
        )
        out.append(
            _mk(
                company,
                job.get("text"),
                job.get("hostedUrl") or "",
                cats.get("location") or "",
                cats.get("commitment") or "",
                published=published,
            )
        )
    return out


def _smartrecruiters(company, board):
    resp = requests.get(
        f"https://api.smartrecruiters.com/v1/companies/{board}/postings?limit=100",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    out = []
    for job in resp.json().get("content", []):
        loc = job.get("location") or {}
        city = ", ".join(p for p in (loc.get("city"), loc.get("country")) if p)
        ad = job.get("jobAd") or {}
        url = (
            f"https://jobs.smartrecruiters.com/{board}/{ad['id']}"
            if ad.get("id")
            else job.get("ref") or ""
        )
        out.append(
            _mk(
                company,
                job.get("name"),
                url,
                "Remote" if loc.get("remote") else city,
                published=(job.get("releasedDate") or "")[:10],
            )
        )
    return out


PLATFORMS = {
    "greenhouse": _greenhouse,
    "lever": _lever,
    "smartrecruiters": _smartrecruiters,
}
