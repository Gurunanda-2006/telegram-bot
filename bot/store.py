import json
import os
from datetime import datetime, timedelta, timezone


class SeenStore:
    def __init__(self, path, retention_days=30):
        self.path = path
        self.retention = retention_days
        self.items = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                self.items = (json.load(fh) or {}).get("items", {})
        except (json.JSONDecodeError, OSError):
            self.items = {}

    def seen(self, item_id):
        return item_id in self.items

    def mark(self, ids):
        now = datetime.now(timezone.utc).isoformat()
        for item_id in ids:
            self.items[item_id] = now

    def prune(self):
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=self.retention)
        ).isoformat()
        self.items = {k: v for k, v in self.items.items() if v >= cutoff}

    def save(self):
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"items": self.items}, fh, indent=1)
        os.replace(tmp, self.path)
