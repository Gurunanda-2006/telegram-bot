import logging

import requests

log = logging.getLogger(__name__)

CHUNK_LIMIT = 3800


def send_message(token, chat_id, text):
    ok = True
    for chunk in chunk_text(text):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=20,
            )
            if resp.status_code != 200:
                log.error("telegram send failed %s %s", resp.status_code, resp.text[:200])
                ok = False
        except requests.RequestException as exc:
            log.error("telegram request error: %s", exc)
            ok = False
    return ok


def chunk_text(text):
    chunks = []
    current = ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= CHUNK_LIMIT:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(block) > CHUNK_LIMIT:
            chunks.append(block[:CHUNK_LIMIT])
            block = block[CHUNK_LIMIT:]
        current = block
    if current:
        chunks.append(current)
    return chunks
