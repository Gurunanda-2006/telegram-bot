# Placement Digest Bot

Every 3 hours, fetches software roles (SDE / SWE / frontend / full-stack / automation) and off-campus drive announcements for the **2027 batch** — internships + full-time, India onsite or remote — and sends a digest to Telegram. Every run is archived as markdown in `digests/`.

```
GitHub Actions (cron every 3h)
  └─ bot/main.py
       ├─ sources/news_rss.py   Google News RSS queries (off-campus drives, 2027 batch)
       ├─ sources/ats.py        live postings: Greenhouse / Lever / SmartRecruiters
       ├─ filters.py            role + entry-level + batch(2027) + geo(India/remote)
       ├─ store.py              seen.json dedupe state
       ├─ digest.py             formats digest, writes digests/<timestamp>.md
       └─ telegram.py           sends to Telegram (auto-splits long messages)
  └─ commits seen.json + digest back to repo
```

## Setup

### 1. Telegram bot (2 minutes)

1. Open Telegram → message **@BotFather** → `/newbot` → follow prompts → copy the **token**
2. Send any message to your new bot, then open:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   Find `"chat":{"id": <number>}` — that number is your **chat id**
3. To send to a **channel/group** instead: add the bot as admin, post once, use the group id (`-100...`) from getUpdates

### 2. GitHub repo

1. Create an empty repo on GitHub (private recommended)
2. Push this folder:

```powershell
cd "C:\Users\GURUNANMDA\OneDrive\Desktop\telegram bot"
git add .
git commit -m "placement digest bot"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

3. Repo → Settings → Secrets and variables → Actions → New repository secret:
   - `TELEGRAM_BOT_TOKEN` = token from BotFather
   - `TELEGRAM_CHAT_ID` = chat id from step 1

### 3. First run

Repo → **Actions** tab → *placement-digest* → **Run workflow**. Verify the Telegram message arrives, then cron takes over every 3 hours.

## Local test (dry run)

```powershell
python -m pip install -r requirements.txt
$env:DRY_RUN="1"
python bot/main.py
Remove-Item Env:DRY_RUN
```

Without secrets set it prints the digest to console instead of sending, and does not touch `seen.json`.

## Customizing (no code changes needed)

| File | What to change |
|---|---|
| `config/companies.yaml` | Add/remove `companies:` entries. Give one an `ats:` platform + `board:` slug to poll live postings; leave without `ats:` for news-only coverage. `careers:` URL powers the apply-link fallback for news items |
| `config/companies.yaml` → `news.queries` | Add/remove Google News search strings |
| `config/keywords.yaml` | Roles, junior-role patterns (`level_patterns`), hiring-signal words, exclusions (`exclude_keywords` / regex `exclude_patterns`), batch year(s), India cities, digest size |

Digest badges: 🏢 live ATS posting · 📰 news/drive announcement · 🎓 entry-level signal detected. Items mentioning **2027** sort first; other freshers/off-campus news backfills after ATS postings.

Apply links: ATS postings always carry their direct application URL (`🔗 Apply:`). News items show the article link plus the company's official careers page (`✅ Apply via careers page:`) when the company is recognized — unrecognized companies get a pointer to check the article/company site instead.

To find a company's ATS board slug, check if its careers page URL contains `greenhouse.io/<slug>`, `lever.co/<slug>`, or `jobs.smartrecruiters.com/<slug>`.

## Notes & caveats

- GitHub Actions cron can fire ~10 min late under load; harmless at 3h cadence
- Scheduled workflows are disabled after 60 days of inactivity — this bot auto-commits each run, keeping itself alive
- Amazon/Google/Microsoft/Flipkart etc. sit behind Workday/custom ATS with no public JSON API; they're covered via news announcements instead
- News links go through Google redirect URLs (normal for Google News RSS)

## Phase 2 (planned): resume-based match scoring

A `profile.yaml` (your skills, preferred roles/cities) will score each posting against you — 🔥 strong match / 👍 relevant / 📄 FYI tags in the digest. Data structures are already normalized to support it.
