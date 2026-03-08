# Waypoint — Kingsford University AI Course Counsellor

Real-time voice AI built for the **Gemini Live Agent Challenge** (deadline Mar 16 2026).
"Clara" is a voice-first course counsellor for the fictional Kingsford University, Melbourne.

## Tech Stack

| Layer | Choice |
|-------|--------|
| Agent | Google ADK (`google-adk`) |
| Model | `gemini-2.5-flash-native-audio-latest` |
| Backend | FastAPI + Uvicorn → Cloud Run |
| Database | Neon (serverless Postgres 17 + pgvector) |
| Frontend | Plain HTML/JS — no build step |
| Session | `InMemorySessionService` (MVP) |

---

## Local Development Setup

### 1. Prerequisites

- Python 3.11+
- A [Neon](https://neon.tech) account (free tier is fine)
- A Google AI Studio API key (`GOOGLE_API_KEY`)

### 2. Clone and create venv

```bash
git clone <repo-url>
cd gemini-live-uni-guide
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
GOOGLE_API_KEY=your-google-ai-studio-key
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
DATABASE_URL=postgresql://...@...neon.tech/neondb?sslmode=require
```

All other values in `.env.example` have sensible defaults for local dev.

### 4. Database setup (Neon)

Create a project at [neon.tech](https://neon.tech), copy the connection string, and paste it into `DATABASE_URL` in `.env`.

Then run the seed script — it applies the schema, inserts seed data, and generates embeddings:

```bash
python backend/seed.py
```

Expected output:
```
Applying schema …
Inserting seed data …
Generating course embeddings …
  Embedded 15 courses.

Database ready: 15 courses, 7 events.
```

---

## Database Schema

### `courses`
| Column | Type | Notes |
|--------|------|-------|
| id | serial PK | |
| code | text UNIQUE | e.g. `CS101` |
| name | text | |
| faculty | text | Engineering & Technology / Business & Commerce / Arts & Humanities / Health Sciences |
| level | text | Undergraduate / Postgraduate |
| study_mode | text | Full-time / Part-time / Online |
| duration_years | numeric | |
| atar_cutoff | integer | NULL = no ATAR required |
| annual_fee_aud | integer | |
| description | text | |
| career_outcomes | text | |
| embedding | vector(1536) | `gemini-embedding-001`, Matryoshka 1536-dim |

### `events`
| Column | Type | Notes |
|--------|------|-------|
| id | serial PK | |
| title | text | |
| event_type | text | OpenDay / InfoSession / CampusTour / Webinar |
| start_at | timestamptz | |
| end_at | timestamptz | |
| location | text | Building/room or "Online" |
| description | text | |
| max_capacity | integer | |
| spots_left | integer | |

### `tour_bookings`
| Column | Type | Notes |
|--------|------|-------|
| id | serial PK | |
| student_name | text | |
| email | text | |
| preferred_date | date | |
| party_size | integer | 1–6 |
| created_at | timestamptz | auto |

### `knowledge_docs` *(reserved for Day 2+ RAG)*
| Column | Type | Notes |
|--------|------|-------|
| id | serial PK | |
| topic | text | admissions / fees / campus-life / etc. |
| title | text | |
| content | text | |
| embedding | vector(1536) | |

**Indexes:** HNSW cosine on `courses.embedding` and `knowledge_docs.embedding`; B-tree on `events(event_type, start_at)`.

---

## Agent Tools

| Tool | Description |
|------|-------------|
| `search_courses(query, faculty?)` | Vector similarity search over courses |
| `recommend_courses(interests, strengths, study_mode?)` | Personalised recommendations with match % |
| `search_events(event_type?, date_range?)` | Upcoming events filtered by type and date |
| `book_campus_tour(name, email, date, party_size)` | Inserts a `tour_bookings` row, returns `GT-NNNNN` ref |
| `display_data(type, data, spoken_summary)` | Side-channel → WebSocket → frontend card |

---

## Project Structure

```
backend/
  agent.py      # ADK Agent "Clara" — model, instruction, tools
  tools.py      # All 5 @tool functions + display_data callback registry
  db.py         # asyncpg pool (used by FastAPI — not by tools directly)
  seed.py       # One-shot schema + seed + embedding script
  main.py       # FastAPI app + WebSocket bridge  [Day 4]
frontend/
  index.html    # Voice UI + card sidebar          [Day 5]
data/
  schema.sql    # CREATE TABLE / CREATE INDEX
  seed.sql      # 15 courses + 7 events (Kingsford University)
  knowledge/    # Markdown docs for RAG            [future]
Dockerfile
cloudbuild.yaml
requirements.txt
.env.example
spike_audio.py  # Day 1 ADK live round-trip spike (keep for reference)
```

---

## Build Status

| Day | Date | Goal | Status |
|-----|------|------|--------|
| 1 | Mar 6 | ADK spike — audio round-trip confirmed | ✅ |
| 2 | Mar 7 | DB schema, seed data, `search_courses`, `search_events` | ✅ |
| 3 | Mar 8 | `recommend_courses`, `book_campus_tour`, `display_data`, `agent.py` | ✅ |
| 4 | Mar 9 | FastAPI WebSocket bridge, audio from browser | ⬜ |
| 5 | Mar 10 | Frontend MVP: mic button, transcript, card sidebar | ⬜ |
| 6 | Mar 11 | Deploy to Cloud Run + Neon | ⬜ |
| 7 | Mar 12 | Polish: barge-in, comparison cards, booking animation | ⬜ |
| 8 | Mar 13 | Demo video | ⬜ |
| 9 | Mar 14 | README, architecture diagram, Devpost draft | ⬜ |
| 10 | Mar 15 | Blog post (dev.to), final submit | ⬜ |
