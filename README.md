# PTCG Battle Log Analyzer (Streamlit)

A simple app to parse **PTCG Live battle logs**, generate match summaries, and save games into a SQLite database for long-term stats.

Player mapping is fixed:
- `Neurologist2024` = **You**
- other player = **Opp**

## What this app does

- Paste one battle log
- Parse turns and key actions
- Track KO + Prize events
- Detect up to 2 turning points:
  - biggest prize swing turn
  - first KO on a Pokemon with `ex` in the name
- Generate 3 markdown outputs:
  - Turn Timeline
  - KO + Prize Tracker table
  - Competitive Summary Template
- Save game + events to `ptcg_logs.db`
- Show database dashboard stats:
  - Overall win rate
  - Win rate by opp deck / your deck
  - Avg turns / avg prize differential
  - Go first vs go second advantage

## Files

- `app.py` - main Streamlit app (single file)
- `sample_log.txt` - sample PTCG Live battle log
- `requirements.txt` - Python dependencies
- `ptcg_logs.db` - local SQLite database (auto-created)

## Quick Start (Local)

### 1) Install Python packages

```bash
python3 -m pip install -r requirements.txt
```

### 2) Run app

```bash
streamlit run app.py
```

### 3) Use the UI

- Paste log in textarea (or use preloaded sample)
- Optional: fill deck names and format/date
- Click:
  - `Generate Summary Only` (no DB write)
  - `Parse & Save` (save into SQLite)

## Database behavior

### Local machine

`ptcg_logs.db` is a normal file in this folder.
- Closing Streamlit does **not** delete data
- Reopening app continues from same DB

### Streamlit Community Cloud

Cloud local files are **not guaranteed permanent**.
- Data may reset on restart/redeploy
- For long-term storage, use external DB (Postgres/Supabase/Neon) or export backups

## Deploy on Streamlit Community Cloud (for your own copy)

This is the recommended way for public sharing: each user deploys from their own GitHub repo.

1. Fork this repository to your GitHub account
2. Open [Streamlit Community Cloud](https://share.streamlit.io)
3. Click **New app**
4. Select your forked repo
5. Branch: `main`
6. Main file path: `app.py`
7. Deploy

## Common issue

### "App code is not connected to a remote GitHub repository"

Your local folder is not enough for Streamlit Cloud.
You must push code to GitHub first, then deploy from that repo.

## Notes

- Parser is regex + state machine (no heavy NLP)
- Works best with English PTCG Live logs
- If `decided to go first` is missing, first/second is stored as `Unknown`
