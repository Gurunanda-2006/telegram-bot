import logging
import os
import sys
from datetime import datetime, timezone

import yaml

from digest import build_digest, build_still_open_digest, write_digest
from filters import ItemFilter, classify, sort_key
from sources.ats import fetch_all_ats
from sources.news_rss import fetch_news
from store import SeenStore
from telegram import send_message

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT, "config")


def load_yaml(name):
    path = os.path.join(CONFIG_DIR, name)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    kw = load_yaml("keywords.yaml")
    comp = load_yaml("companies.yaml")
    settings = kw.get("settings", {})
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    dry_run = os.environ.get("DRY_RUN") == "1" or not (token and chat_id)

    company_names = [c.get("name", "") for c in comp.get("companies", [])]
    raw = fetch_news(comp.get("news", {}), kw, company_names)
    raw += fetch_all_ats(comp)

    item_filter = ItemFilter(kw)
    kept = sorted(
        (classify(i, item_filter) for i in raw if item_filter.passes(i)),
        key=sort_key,
    )

    store_path = os.path.join(ROOT, "seen.json")
    retention = settings.get("state_retention_days", 30)
    store = SeenStore(store_path, retention)
    new = [i for i in kept if not store.seen(i["id"])]

    still_open_max = settings.get("still_open_max", 4)
    ats_seen = [i for i in kept if i["source"] == "ats" and store.seen(i["id"])]
    news_seen = [
        i
        for i in kept
        if i["source"] == "news" and i.get("news_tier") == 0 and store.seen(i["id"])
    ]
    still_open = (ats_seen + news_seen)[:still_open_max]

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d-%H%M")
    label = now.strftime("%Y-%m-%d %H:%M UTC")

    max_items = settings.get("max_items_per_digest", 15)
    shown = new[:max_items]
    careers = {
        c.get("name", "").lower(): c.get("careers")
        for c in comp.get("companies", [])
        if c.get("careers")
    }

    send_empty = settings.get("send_empty_digest", True)
    if shown:
        text = build_digest(shown, len(new), label, careers, still_open)
    elif send_empty and still_open:
        text = build_still_open_digest(label, len(raw), still_open)
    elif send_empty:
        text = (
            f"🟢 No new openings or significant updates in the last 3 hours — {label}\n"
            f"Scanned {len(raw)} listings from the internet.\n"
            f"Next check in 3 hours."
        )
    else:
        text = ""

    if text:
        if dry_run:
            print("\n--- DRY RUN (no secrets set) ---")
            print(text)
        elif not send_message(token, chat_id, text):
            logging.error("telegram delivery failed; state not updated; will retry next run")
            sys.exit(1)
        write_digest(os.path.join(ROOT, "digests"), stamp, text)

    store.mark(i["id"] for i in shown)
    if not dry_run:
        store.prune()
        store.save()
    print(f"fetched={len(raw)} matched={len(kept)} new={len(new)} sent={len(shown)}")


if __name__ == "__main__":
    main()
