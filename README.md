# 🎯 SkillMap - Career Tracker

SkillMap helps students and interns prepare for their first tech job. Pick a career path,
learn the right skills, finish practical tasks, practice interview questions and track your
readiness with a personal dashboard and a downloadable PDF report.

## Features

- **Accounts** - sign up / log in, salted PBKDF2 password hashing, login lockout after 5 failed attempts,
  stay logged in, SQLite or permanent PostgreSQL storage
- **Learning Resources** - curated tutorials per skill, status saved per user, filter by status
- **Action Plan** - practical tasks with a "proof of work" link (GitHub / portfolio)
- **Study Tracker** - log sessions, daily streak, weekly goal, 14-day chart
- **Interview Prep** - technical + HR questions with hints and "practiced" tracking
- **Dashboard** - weighted career readiness score (skills 50%, tasks 30%, interview 20%),
  achievements, skill-gap analyzer, overview of all career paths
- **Reports** - TXT, CSV and PDF downloads
- **Profile** - edit name and goal, change password, delete account and all data

## Project structure

```
app.py            Streamlit app (all pages)
database.py       SQLite layer (users, progress, study logs)
skills_data.py    Career paths and skills (edit this to add roles)
content.py        Practical tasks and interview questions
theme.py          CSS theme and hero banner
report.py         PDF report (reportlab)
assets/           Banner image
tests/            Unit tests for the database layer
.streamlit/       Streamlit theme and server settings
```

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

Run the tests: `python -m unittest tests.test_database tests.test_postgres_adapter -v`

## Add a new career path

1. Add the role and its skills to `skills_data.py`.
2. (Optional) Add practical tasks to `ACTION_PLANS` and questions to `INTERVIEW_QUESTIONS` in `content.py`
   using the same role name. Roles without tasks/questions still work; those areas are simply skipped
   in the readiness score.

## Permanent data (PostgreSQL) and staying logged in

**Database.** Without configuration SkillMap uses a local SQLite file. That is perfect for
development, but on free cloud hosts the disk is wiped on restart. To keep accounts and progress
forever, connect a free PostgreSQL database (for example **Neon** or **Supabase**):

1. Create a free project at <https://neon.tech> and copy the connection string
   (it looks like `postgresql://user:password@host/dbname?sslmode=require`).
2. Local test: create `.streamlit/secrets.toml` containing `DATABASE_URL = "..."`
   (see `.streamlit/secrets.toml.example`).
3. Streamlit Cloud: App -> Settings -> Secrets -> paste the same line.
4. Restart the app. **Profile -> Database** should now say *PostgreSQL*.

The app creates all tables automatically on first start. You can also set `DATABASE_URL`
as an environment variable (Docker, Render, Railway, ...).

> Supabase: use the **Session pooler** connection string (the direct host is IPv6-only).

## Deploy

### Option A - Streamlit Community Cloud (free)

1. Push this folder to GitHub (the `.gitignore` already excludes database files and secrets).
2. Go to <https://share.streamlit.io>, click **New app**, pick the repo, branch and `app.py`.
3. Open **Settings -> Secrets** and add your `DATABASE_URL` (see above).
4. Deploy. You get an HTTPS link to share.

### Option B - Docker with a persistent volume (Render, Railway, Fly.io, any VPS)

```bash
docker build -t skillmap .
docker run -p 8501:8501 -v skillmap_data:/data skillmap
```

Without `DATABASE_URL` the SQLite file lives in `/data/skillmap_app.db` (set with `SKILLMAP_DB`).
Attach a persistent disk/volume at `/data`, or simply set `DATABASE_URL` and use PostgreSQL.

## Notes

- The PDF uses built-in fonts, so characters outside Latin-1 (for example Urdu names) are shown as `?` in the PDF.
- The old single-user `skillmap.db` is not used by this version. Without `DATABASE_URL`, progress is stored in `skillmap_app.db`.
- The PostgreSQL code path is covered by adapter tests with a fake driver; always do one real test with your own database after connecting.
