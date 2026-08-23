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


def build_digest(items, total_new, run_label, careers=None):
    careers = careers or {}
    lines = [f"🎯 Placement Digest — {run_label}", f"{total_new} new for 2027 batch", ""]
    for it in items:
        badge = "🏢" if it["source"] == "ats" else "📰"
        if it.get("entry_level"):
            badge += "🎓"
        lines.append(f"{badge} {it['company'] or 'Hiring News'} — {it['title']}")
        meta = [p for p in (it.get("location"), it.get("employment")) if p]
        if meta:
            lines.append("📍 " + " · ".join(meta))
        lines.extend(_apply_lines(it, careers))
        lines.append("")
    return "\n".join(lines).strip()


def write_digest(digests_dir, run_stamp, text):
    os.makedirs(digests_dir, exist_ok=True)
    path = os.path.join(digests_dir, f"{run_stamp}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    return path
