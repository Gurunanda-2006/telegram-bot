import re


def _contains(text, terms):
    lowered = (text or "").lower()
    return any(term.lower() in lowered for term in terms)


class ItemFilter:
    def __init__(self, keywords):
        self.kw = keywords
        self.level_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in keywords.get("level_patterns", [])
        ]
        self.exclude_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in keywords.get("exclude_patterns", [])
        ]

    def passes(self, item):
        title = item.get("title") or ""
        location = item.get("location") or ""
        extra = item.get("extra_text") or ""
        combined = f"{title} {extra}"
        if _contains(title, self.kw.get("exclude_keywords", [])):
            return False
        if any(p.search(title) for p in self.exclude_patterns):
            return False
        if not (
            _contains(title, self.kw["role_keywords"])
            or _contains(extra, self.kw["role_keywords"])
        ):
            return False
        if item["source"] == "ats":
            if not self._geo_ok(location):
                return False
            if self.kw.get("settings", {}).get("require_entry_signal", False):
                return self.is_entry_level(title) or self._batch_hit(combined)
            return True
        if not _contains(combined, self.kw["hiring_signals"]):
            return False
        item["news_tier"] = 0 if re.search(r"\b2027\b", combined) else 1
        return True

    def is_entry_level(self, text):
        if _contains(text, self.kw["level_keywords"]):
            return True
        return any(p.search(text or "") for p in self.level_patterns)

    def _batch_hit(self, text):
        for pattern in self.kw.get("batch_patterns", []):
            if re.search(rf"\b{re.escape(str(pattern))}\b", text or ""):
                return True
        return False

    def _geo_ok(self, location):
        geo = self.kw["geo"]
        if not (location or "").strip():
            return True
        allowed = [t.lower() for t in geo["india_terms"]] + [
            t.lower() for t in geo["remote_terms"]
        ]
        return _contains(location, allowed)


def sort_key(item):
    if item["source"] == "news":
        return (0, "") if item.get("news_tier") == 0 else (2, "")
    return (1, "")


def classify(item, item_filter=None):
    title = item.get("title") or ""
    lowered = title.lower()
    if not item.get("employment"):
        if any(t in lowered for t in ("intern", "internship", "trainee")):
            item["employment"] = "Internship"
        else:
            item["employment"] = "Full-time"
    if item_filter is not None:
        item["entry_level"] = bool(
            item_filter.is_entry_level(title)
            or re.search(r"\b2027\b", f"{title} {item.get('extra_text') or ''}", re.I)
        )
    return item
