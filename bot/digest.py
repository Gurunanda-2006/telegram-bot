import os


def _apply_lines(item, careers):
    if item["source"] == "ats":
        return [f"🔗 Apply: {item['url']}"]
    lines = [f"📰 Details: {item['url']}"]
    careers_url = careers.get((item.get("company") or "").lower())
    if careers_url:
        lines.append(f"✅ Apply via careers page: {careers_url}")
    else:
        lines.append("ℹ️ No direct apply link yet — see article or company careers page")
    return lines


def _item_line(it, careers):
    badge = "🏢" if it["source"] == "ats" else "📰"
    if it.get("entry_level"):
        badge += "🎓"
    lines = [f"{badge} {it['company'] or 'Hiring News'} — {it['title']}"]
    meta = [p for p in (it.get("location"), it.get("employment")) if p]
    if meta:
        lines.append("📍 " + " · ".join(meta))
    lines.extend(_apply_lines(it, careers))
    return lines


def _still_open_lines(still_open):
    lines = ["📌 Still open — live postings from earlier scans:", ""]
    for it in still_open:
        badge = "🏢" if it["source"] == "ats" else "📰"
        lines.append(f"{badge} {it['company'] or 'Hiring News'} — {it['title']}")
        lines.append(f"🔗 {it['url']}")
        lines.append("")
    return lines


def build_digest(items, total_new, run_label, careers=None, still_open=None):
    careers = careers or {}
    lines = [f"🎯 Placement Digest — {run_label}", f"{total_new} new for 2027 batch", ""]
    for it in items:
        lines.extend(_item_line(it, careers))
        lines.append("")
    if still_open:
        lines.extend(_still_open_lines(still_open))
    return "\n".join(lines).strip()


def build_still_open_digest(run_label, scanned, still_open):
    lines = [
        f"🟢 No new openings in the last 3 hours — {run_label}",
        f"Scanned {scanned} listings · next check in 3 hours.",
        "",
    ]
    lines.extend(_still_open_lines(still_open))
    return "\n".join(lines).strip()


def build_heartbeat(run_label, scanned, still_open_count):
    text = (
        f"🟢 No new openings or significant updates in the last 3 hours — {run_label}\n"
        f"Scanned {scanned} listings from the internet.\n"
        f"Next check in 3 hours."
    )
    if still_open_count:
        text += f"\n({still_open_count} earlier openings still listed below)"
    return text


def write_digest(digests_dir, run_stamp, text):
    os.makedirs(digests_dir, exist_ok=True)
    path = os.path.join(digests_dir, f"{run_stamp}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    return path
