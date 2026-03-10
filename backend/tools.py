"""
Waypoint ADK tools.
All tools must be synchronous (ADK calls them in a thread pool).
"""
import asyncio
import logging
import os
from datetime import date
from typing import Any, Callable, Coroutine, Optional

import google.genai as genai
import google.genai.types as genai_types

_genai_client: genai.Client | None = None
log = logging.getLogger(__name__)

def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _genai_client

# ── display_data side-channel ─────────────────────────────────────────────────
# Day 4 WebSocket bridge registers an async callback here per session.
# display_data calls it via run_coroutine_threadsafe so the frontend gets cards
# without waiting for the model to finish speaking.

_display_callbacks: dict[str, tuple[asyncio.AbstractEventLoop, Callable]] = {}


def register_display_callback(
    session_id: str,
    loop: asyncio.AbstractEventLoop,
    callback: Callable[[dict], Coroutine],
) -> None:
    _display_callbacks[session_id] = (loop, callback)


def unregister_display_callback(session_id: str) -> None:
    _display_callbacks.pop(session_id, None)

# ── Embedding helper ──────────────────────────────────────────────────────────

from functools import lru_cache

@lru_cache(maxsize=64)
def _embed(text: str) -> tuple[float, ...]:
    """Embed text via Gemini. Results are LRU-cached to avoid repeated API calls."""
    result = _get_genai_client().models.embed_content(
        model="gemini-embedding-001",
        contents=[text],
        config=genai_types.EmbedContentConfig(output_dimensionality=1536),
    )
    return tuple(result.embeddings[0].values)


def _emb_str(values) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def _to_json_safe(row: dict) -> dict:
    """Convert psycopg2 row to JSON-safe Python primitives.

    NUMERIC(3,1) maps to Decimal, which json.dumps can't handle.
    Also truncates long text fields to keep function responses small.
    """
    from decimal import Decimal
    result = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            result[k] = float(v)
        elif isinstance(v, str) and k in ("career_outcomes", "description") and len(v) > 150:
            result[k] = v[:150] + "…"
        else:
            result[k] = v
    return result


# ── DB helper (sync via asyncpg run_until_complete workaround) ────────────────
# Tools run in a thread; we use a fresh psycopg2 connection per call
# to stay fully synchronous without event-loop gymnastics.

import psycopg2
import psycopg2.extras
import psycopg2.pool

_pg_pool: psycopg2.pool.ThreadedConnectionPool | None = None

def _get_pg_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1, maxconn=5, dsn=os.environ["DATABASE_URL"]
        )
    return _pg_pool

from contextlib import contextmanager

@contextmanager
def _get_conn():
    pool = _get_pg_pool()
    conn = pool.getconn()
    try:
        conn.autocommit = True
        yield conn
    finally:
        pool.putconn(conn)


# ── Tool 1: search_courses ────────────────────────────────────────────────────

def search_courses(query: str, faculty: Optional[str] = None) -> dict:
    """
    Search Kingsford University courses by a natural-language query.
    Optionally filter by faculty (e.g. 'Engineering & Technology', 'Business & Commerce',
    'Arts & Humanities', 'Health Sciences').
    Returns up to 5 matching courses with key details.
    """
    log.debug("search_courses query='%s' faculty=%s", query, faculty)
    emb = _emb_str(_embed(query))
    log.debug("Embedding generated, executing SQL...")
    sql = """
        SELECT code, name, faculty, level, study_mode,
               duration_years, atar_cutoff, annual_fee_aud,
               career_outcomes,
               1 - (embedding <=> %s::vector) AS similarity
        FROM courses
        WHERE (%s::text IS NULL OR faculty ILIKE %s)
        ORDER BY embedding <=> %s::vector
        LIMIT 5
    """
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (emb, faculty, f"%{faculty}%" if faculty else None, emb))
            rows = cur.fetchall()
            log.debug("SQL executed, found %d rows", len(rows))
        courses = [_to_json_safe(dict(r)) for r in rows]
        data = {"courses": courses, "count": len(rows)}
        
        # Directly emit card to ensure delivery
        if _display_callbacks:
            payload = {"type": "card", "card_type": "courses", "data": data, "spoken_summary": "Here are some matching courses."}
            for loop, callback in _display_callbacks.values():
                asyncio.run_coroutine_threadsafe(callback(payload), loop)
                
        return data


# ── Tool 2: search_events ────────────────────────────────────────────────────

def search_events(event_type: Optional[str] = None, date_range: Optional[str] = None) -> dict:
    """
    Search upcoming Kingsford University events.
    event_type: one of OpenDay, InfoSession, CampusTour, Webinar (or None for all).
    date_range: optional ISO date range like '2026-03-10,2026-03-20' (or None for next 30 days).
    Returns matching events with title, type, date, location, and spots remaining.
    """
    from datetime import datetime, timedelta, timezone

    now = datetime.now(tz=timezone.utc)
    if date_range:
        parts = date_range.split(",")
        date_from = parts[0].strip()
        date_to   = parts[1].strip() if len(parts) > 1 else (now + timedelta(days=30)).date().isoformat()
    else:
        date_from = now.date().isoformat()
        date_to   = (now + timedelta(days=30)).date().isoformat()

    sql = """
        SELECT id, title, event_type, start_at, end_at, location,
               description, spots_left
        FROM events
        WHERE (%s::text IS NULL OR event_type ILIKE %s)
          AND start_at >= %s::date
          AND start_at <  %s::date + INTERVAL '1 day'
        ORDER BY start_at
        LIMIT 10
    """
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (
                event_type, f"%{event_type}%" if event_type else None,
                date_from, date_to,
            ))
            rows = cur.fetchall()

    events = []
    for r in rows:
        d = dict(r)
        d["start_at"] = d["start_at"].isoformat() if d["start_at"] else None
        d["end_at"]   = d["end_at"].isoformat()   if d["end_at"]   else None
        events.append(d)

    data = {"events": events, "count": len(events)}
    
    # Directly emit card to ensure delivery
    if _display_callbacks:
        payload = {"type": "card", "card_type": "events", "data": data, "spoken_summary": "Here are some upcoming events."}
        for loop, callback in _display_callbacks.values():
            asyncio.run_coroutine_threadsafe(callback(payload), loop)
            
    return data


# ── Tool 3: recommend_courses ─────────────────────────────────────────────────

def recommend_courses(
    interests: str,
    strengths: str,
    study_mode_preference: Optional[str] = None,
) -> dict:
    """
    Recommend Kingsford University courses tailored to a student's interests,
    strengths, and preferred study mode.
    interests: free-text description of what the student enjoys (e.g. 'maths, problem solving').
    strengths: free-text description of their academic strengths (e.g. 'sciences, writing').
    study_mode_preference: 'Full-time', 'Part-time', 'Online', or None for any.
    Returns up to 4 recommended courses with a match score and brief rationale.
    """
    query = f"student interested in {interests} with strengths in {strengths}"
    emb = _emb_str(_embed(query))

    mode_filter = ""
    params: list[Any] = [emb]
    if study_mode_preference:
        mode_filter = "AND study_mode ILIKE %s"
        params.append(f"%{study_mode_preference}%")
    params.append(emb)

    sql = f"""
        SELECT code, name, faculty, level, study_mode,
               duration_years, atar_cutoff, annual_fee_aud,
               career_outcomes,
               1 - (embedding <=> %s::vector) AS similarity
        FROM courses
        WHERE 1=1 {mode_filter}
        ORDER BY embedding <=> %s::vector
        LIMIT 4
    """
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    results = []
    for r in rows:
        d = _to_json_safe(dict(r))
        d["match_pct"] = round(float(d["similarity"]) * 100)
        results.append(d)

    data = {
        "recommendations": results,
        "count": len(results),
        "query_summary": query,
    }
    
    # Directly emit card
    if _display_callbacks:
        payload = {"type": "card", "card_type": "courses", "data": {"courses": results, "count": len(results)}, "spoken_summary": "I recommend these courses based on your interests."}
        for loop, callback in _display_callbacks.values():
            asyncio.run_coroutine_threadsafe(callback(payload), loop)
            
    return data


# ── Tool 4: book_campus_tour ──────────────────────────────────────────────────

def book_campus_tour(
    student_name: str,
    email: str,
    preferred_date: str,
    party_size: int = 1,
) -> dict:
    """
    Book a campus tour at Kingsford University.
    preferred_date: ISO date string, e.g. '2026-03-15'.
    party_size: number of people attending (including the student), max 6.
    Returns a booking confirmation with a reference ID.
    """
    if party_size < 1 or party_size > 6:
        return {"success": False, "error": "party_size must be between 1 and 6"}

    try:
        tour_date = date.fromisoformat(preferred_date)
    except ValueError:
        return {"success": False, "error": f"Invalid date format: {preferred_date}. Use YYYY-MM-DD."}

    sql = """
        INSERT INTO tour_bookings (student_name, email, preferred_date, party_size)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at
    """
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (student_name, email, tour_date, party_size))
            row = dict(cur.fetchone())

    data = {
        "success": True,
        "booking_id": f"GT-{row['id']:05d}",
        "student_name": student_name,
        "email": email,
        "preferred_date": preferred_date,
        "party_size": party_size,
        "message": (
            f"Tour booked! Your reference is GT-{row['id']:05d}. "
            f"A confirmation will be sent to {email}."
        ),
    }

    if _display_callbacks:
        payload = {"type": "card", "card_type": "booking", "data": data, "spoken_summary": "Your tour is booked!"}
        for loop, callback in _display_callbacks.values():
            asyncio.run_coroutine_threadsafe(callback(payload), loop)
            
    return data


# ── Tool 5: display_data ──────────────────────────────────────────────────────

def display_data(type: str, data: dict, spoken_summary: str) -> dict:
    """
    Send structured data to the student's browser as a visual card.
    Call this alongside every substantive spoken response so the UI shows details.
    type: 'courses', 'events', 'booking', 'info'.
    data: the structured payload to render (course list, event list, booking confirmation, etc.).
    spoken_summary: the short spoken version already being said (≤50 words).
    Returns immediately; card delivery is async via WebSocket.
    """
    payload = {"type": "card", "card_type": type, "data": data, "spoken_summary": spoken_summary}

    if _display_callbacks:
        for loop, callback in _display_callbacks.values():
            asyncio.run_coroutine_threadsafe(callback(payload), loop)
    else:
        # No WebSocket yet (testing) — log to console
        import json
        print(f"[display_data] {type}: {json.dumps(data, default=str)[:120]} …")

    return {"delivered": True, "type": type}
