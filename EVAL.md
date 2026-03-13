# Waypoint Evaluation Suite

Automated tests for Clara's tools and routing logic. Two layers, no voice required.

## Quick start

```bash
# Full suite (DB + routing + multi-turn):
python eval_suite.py

# Layer 1 only — tool correctness against real DB (no extra API quota):
python eval_suite.py --layer1-only

# Layer 2 only — single-turn routing via Gemini text API (no DB write needed):
python eval_suite.py --layer2-only

# Layer 2b only — multi-turn conversation routing:
python eval_suite.py --layer2b-only

# Skip multi-turn (faster run — Layer 1 + Layer 2 only):
python eval_suite.py --no-multiturn
```

Reads `.env` automatically — no need to export vars first.
Writes a machine-readable report to `eval_report.json`.

---

## Layer 1 — Tool Correctness

Calls each tool function **directly** against the live DB and asserts on the response shape.

| Tool | Test cases | What passing means |
|------|-----------|-------------------|
| `get_course_detail` | 2 | pgvector lookup returns a course with name, faculty, career_outcomes, fee; non-matching name returns graceful fallback (closest match) |
| `search_courses` | 3 | semantic search returns ≥1 result; faculty filter narrows correctly |
| `recommend_courses` | 2 | interest/strength query returns ≥1 result; study mode filter works |
| `search_events` | 2 | upcoming events returned; type filter (CampusTour) works |
| `search_knowledge` | 6 | 6 distinct knowledge topics each return a non-empty excerpt (ATAR, HECS, visa, accommodation, careers, facilities) |
| `search_scholarships` | 5 | general + all 4 type filters (Merit, Equity, International, Faculty) work; International returns exactly 1 (data integrity check) |
| `book_campus_tour` | 3 | valid booking succeeds + gets `GT-XXXXX` ID; `party_size > 6` rejected; invalid date format rejected |

**Total: 23 assertions across 8 tools.**

**What it does not test:**
- Whether the *right* result is returned — only that *something* is returned
- Result quality or semantic accuracy
- The `display_data` card side-channel (no WebSocket in test context)
- Course description/career_outcomes content (only shape is checked)

---

## Layer 2 — Tool Routing

Sends 24 natural-language queries to **Gemini text API** with Clara's system prompt and tool
declarations. Checks that the model selects the expected tool (or none).

| ID | Query type | Expected tool |
|----|-----------|---------------|
| R00 | Course detail — named course drill-down (e.g. "tell me more about Bachelor of Nursing") | `get_course_detail` |
| R01–R03 | Course search — direct field of study, program framing, health faculty | `search_courses` |
| R04–R06 | Personalised recommendation — interests + strengths, mode preference, creative | `recommend_courses` |
| R07–R09 | Event / open day / info session | `search_events` |
| R10 | Campus tour booking (with full details) | `book_campus_tour` |
| R11–R16 | Knowledge base: ATAR, HECS-HELP, visa, accommodation, facilities, careers | `search_knowledge` |
| R17–R20 | Scholarships: general, international, merit, equity | `search_scholarships` |
| R21–R23 | Greeting, thanks, "what can you do" | `null` (no tool) |

**What it does not test:**
- The live voice pipeline (`gemini-live-2.5-flash-native-audio` via ADK)
- Clara's spoken response quality after receiving tool results
- The WebSocket bridge or card UI rendering (course detail card, markdown info cards)
- Multi-turn conversation coherence (each query is single-shot)
- Cloud Run / Cloud SQL (Layer 1 hits Neon, not Cloud SQL)

### Model gap: `gemini-2.5-flash` vs `gemini-2.5-flash-native-audio`

Layer 2 and 2b use `gemini-2.5-flash` (standard text API). The production agent runs on `gemini-2.5-flash-native-audio` — a separately fine-tuned variant optimised for real-time audio. Three gaps result:

| Gap | Impact | Mitigation |
|-----|--------|-----------|
| **Different model variant** | Native audio may have subtly different tool-calling tendencies. Both share the same base weights so routing is *likely* consistent, but not guaranteed. | Manual voice run-through required before submission. |
| **Simplified routing prompt** | Layer 2/2b use `_ROUTING_SYSTEM` (8 routing rules). Production uses the full `INSTRUCTION` (60+ lines: TURN ISOLATION, DO NOT CALL TOOLS cases, persona, flow). The verbose instruction has caused misrouting in the past (session 7 hallucination fix). | Add `--full-prompt` flag to run Layer 2/2b with the full `INSTRUCTION` for a closer match (not yet implemented). |
| **Clean text vs transcribed speech** | Eval queries are typed, clean sentences. Production receives ADK transcripts of spoken audio — including filler words ("um", "like"), incomplete sentences, and mispronunciations. e.g. real session: *"Um Well, tell me more about scholarships."* vs eval: *"Tell me more about scholarships."* | Routing still passed in observed sessions, but edge cases (e.g. heavily accented speech, crosstalk) are untested. |

**Conclusion**: Layer 2/2b give strong assurance that the *intent → tool mapping* in the instruction is correct in principle. They do not validate that the full instruction + native audio model + transcribed speech produces the same routing in practice. A manual voice run-through covering all 8 tool paths is required alongside the automated suite.

---

## Layer 2b — Multi-Turn Conversation Routing

Sends full multi-turn conversations to **Gemini text API**, checking that Clara routes each turn correctly given the prior context. After each turn, a synthetic model stub response is injected into history so subsequent turns have realistic context.

| ID | Scenario | Turns | What it tests |
|----|----------|-------|---------------|
| MT01 | Full counselling journey (mirrors real session) | 5 | `search_courses` → `get_course_detail` → `search_scholarships` → `search_knowledge` → `search_events` |
| MT02 | Health pathway | 4 | `search_courses` → `get_course_detail` → `search_knowledge` (ATAR) → `search_scholarships` |
| MT03 | Recommendation → detail → knowledge → booking | 4 | `recommend_courses` → `get_course_detail` → `search_knowledge` → `book_campus_tour` |
| MT04 | Context retention (vague follow-up reference) | 4 | `search_courses` → `get_course_detail` (from context) → `search_scholarships` → `search_events` |

**Total: 4 conversations, 17 turns.**

Key routing challenges tested beyond Layer 2:
- **Context-aware detail routing**: After asking about engineering courses, "tell me more about the cybersecurity one" should route to `get_course_detail` — the model must infer the course name from prior context.
- **Topic switching**: Moving from courses → scholarships → knowledge → events in a single session without derailing.
- **Conversational drift**: Vague phrases like "more about the university itself" mid-conversation should still route to `search_knowledge`.

**What it does not test:**
- Whether the model passes the correct arguments to each tool (only the tool name is checked)
- Real conversation history from the live voice pipeline (stubs are synthetic text, not actual tool results)
- Timing between turns

---

## Layer 3 — Vision Flows (manual only)

`data/eval_queries.json` contains 6 vision test cases (V01–V06). These are **manual
checklists**, not automated — they require real images shared via the voice UI.

| ID | Image type | Expected two-turn journey |
|----|-----------|-----------------------------|
| V01 | Student artwork | Describe → offer `search_courses` (Creative Arts) |
| V02 | Merit award certificate | Acknowledge achievement → offer `search_scholarships` |
| V03 | School report card | Discuss grades → offer `search_knowledge` (ATAR) |
| V04 | Hospital / clinical setting | Connect to health programs → `search_courses` |
| V05 | Passport / international context | Mention visa/support → `search_knowledge` |
| V06 | Campus building photo | Invite visit → `book_campus_tour` |

---

## Card UI — manual checks

These require a live browser session and cannot be automated:

| Scenario | What to verify |
|----------|---------------|
| Ask about a field of study | **Courses card** appears with 5 course tiles (name, tags, career outcomes, fee/ATAR row) |
| Say "tell me more about [course name]" | **Course Detail card** appears — 2×2 grid (Duration, Fee, Entry, Code) + full About + Career Outcomes sections |
| Ask about ATAR / HECS / campus life | **Info card** appears with markdown rendered — headings, tables, and bold text formatted correctly (not raw `###`) |
| Ask about scholarships | **Scholarships card** appears with value/yr, duration, eligibility, deadline |
| Book a tour | **Booking card** appears with `GT-XXXXX` reference |

---

## What "all passing" means in practice

| Signal | Covered |
|--------|---------|
| DB is reachable and data is fully seeded (15 courses, 10 events, 55 knowledge chunks, 8 scholarships) | ✓ Layer 1 |
| All 8 tools return non-empty, well-shaped responses | ✓ Layer 1 |
| `get_course_detail` returns full course (no truncation) | ✓ Layer 1 |
| Scholarships data integrity (exactly 1 International row) | ✓ Layer 1 |
| Booking validation logic (date, party_size) | ✓ Layer 1 |
| Clara's system prompt routes all 8 use cases correctly | ✓ Layer 2 |
| Clara distinguishes detail requests (→ `get_course_detail`) from search (→ `search_courses`) | ✓ Layer 2 (R00 vs R01–R03) |
| Clara correctly suppresses tool calls for greetings/chat | ✓ Layer 2 (R21–R23) |
| Clara routes correctly across a full multi-turn counselling session (17 turns, 4 conversations) | ✓ Layer 2b |
| Context-aware routing: vague follow-up ("that one", "the university") resolves correctly | ✓ Layer 2b (MT01, MT04) |
| Course detail card renders with full description + career outcomes | ✗ Manual (Layer 3 card UI) |
| Info card markdown renders correctly (tables, headings) | ✗ Manual (Layer 3 card UI) |
| Voice pipeline (ADK → Gemini Live → audio output) | ✗ Manual |
| Multi-turn conversation coherence | ✗ Manual |
| Production Cloud SQL (Layer 1 hits Neon) | ✗ Manual |

The eval suite + a manual voice run-through of the demo script together give sufficient
confidence for submission. Neither alone is enough.

---

## Adding new tests

**Layer 1** — add a `check(...)` call in `run_layer1()` in `eval_suite.py`.

**Layer 2** — add a JSON object to `data/eval_queries.json` with:
```json
{
  "id": "R25",
  "layer": 2,
  "description": "Short description",
  "query": "The student query string",
  "expected_tool": "tool_name_or_null"
}
```

**Layer 3 (vision)** — add a `layer: 3` object with `turn_1` / `turn_2` structure
following the existing V01–V06 pattern.
