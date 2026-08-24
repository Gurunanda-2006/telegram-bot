import calendar
import hashlib
import html
import logging
import re
import time
import urllib.parse

import feedparser

log = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")


def _make_id(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _clean(text):
    return TAG_RE.sub("", html.unescape(text or "")).strip()


def _strip_publisher(title):
    parts = title.rsplit(" - ", 1)
    if len(parts) == 2 and len(parts[1]) < 40:
        return parts[0].strip()
    return title.strip()


def fetch_news(news_cfg, keywords_cfg, company_names):
    items = []
    known = {name.lower(): name for name in company_names}
    base = news_cfg.get("base_url", "https://news.google.com/rss/search")
    hl = news_cfg.get("hl", "en-IN")
    gl = news_cfg.get("gl", "IN")
    ceid = news_cfg.get("ceid", "IN:en")
    max_age = news_cfg.get("max_age_days", 7)
    for query in news_cfg.get("queries", []):
        url = (
            f"{base}?q={urllib.parse.quote(query)}"
            f"&hl={urllib.parse.quote(hl)}&gl={gl}&ceid={urllib.parse.quote(ceid)}"
        )
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                log.warning("news feed failed for %r", query)
                continue
            for entry in feed.entries[:25]:
                title = _clean(entry.get("title"))
                link = entry.get("link")
                if not title or not link:
                    continue
                published = entry.get("published_parsed")
                if published and max_age:
                    age_days = (time.time() - calendar.timegm(published)) / 86400
                    if age_days > max_age:
                        continue
                lowered = title.lower()
                company = next(
                    (orig for low, orig in known.items() if low in lowered), ""
                )
                items.append(
                    {
                        "id": _make_id(link),
                        "source": "news",
                        "company": company,
                        "title": _strip_publisher(title),
                        "url": link,
                        "location": "",
                        "employment": "",
                        "published": entry.get("published", ""),
                        "extra_text": _clean(entry.get("summary", ""))[:400],
                    }
                )
        except Exception as exc:
            log.warning("error fetching %r: %s", query, exc)
    seen = set()
    unique = [i for i in items if not (i["id"] in seen or seen.add(i["id"]))]
    log.info("news: %d raw items", len(unique))
    return unique
