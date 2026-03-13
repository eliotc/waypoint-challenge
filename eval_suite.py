#!/usr/bin/env python3
"""
Waypoint Evaluation Suite
=========================
Two-layer evaluation for all 7 Clara tools.

Layer 1 — Tool Correctness: calls each tool directly against the real DB and
           asserts on result shape, counts, and expected fields.

Layer 2 — Tool Routing: sends natural-language queries to Gemini (text mode,
           zero-cost vs. audio) and checks whether the model selects the
           expected tool. No actual tool execution.

Usage
-----
    # Run both layers (default):
    DATABASE_URL=<dsn> GOOGLE_API_KEY=<key> python eval_suite.py

    # Skip Gemini routing tests:
    DATABASE_URL=<dsn> GOOGLE_API_KEY=<key> python eval_suite.py --layer1-only

    # Skip direct tool tests:
    GOOGLE_API_KEY=<key> python eval_suite.py --layer2-only

    # Custom queries file:
    python eval_suite.py --queries data/eval_queries.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Auto-load .env from project root so DATABASE_URL / GOOGLE_API_KEY are available
# without requiring the caller to export them first.
def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(env_path, override=False)
        return
    except ImportError:
        pass
    # Fallback: manual parse
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)

_load_dotenv(Path(__file__).parent / ".env")

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def _fail(msg): print(f"  {RED}✗{RESET} {msg}")
def _skip(msg): print(f"  {YELLOW}~{RESET} {msg}")
def _head(msg): print(f"\n{BOLD}{CYAN}{msg}{RESET}")


# ── Layer 1: Direct tool tests ─────────────────────────────────────────────────

def run_layer1() -> list[dict]:
    _head("Layer 1: Tool Correctness (Direct DB Calls)")

    # tools.py lives in backend/; add it to path
    sys.path.insert(0, str(Path(__file__).parent / "backend"))

    from tools import (
        book_campus_tour,
        get_course_detail,
        recommend_courses,
        search_courses,
        search_events,
        search_knowledge,
        search_scholarships,
    )

    results: list[dict] = []

    def check(name: str, fn, args: list, kwargs: dict, assertions):
        t0 = time.monotonic()
        try:
            result = fn(*args, **kwargs)
            latency_ms = round((time.monotonic() - t0) * 1000)
            failures = []
            for desc, ok in assertions(result):
                if ok:
                    _ok(f"{name}: {desc}  ({latency_ms}ms)")
                else:
                    _fail(f"{name}: {desc}  — got: {result!r}")
                    failures.append(desc)
            results.append({
                "test": name,
                "passed": len(failures) == 0,
                "failures": failures,
                "latency_ms": latency_ms,
            })
        except Exception as exc:
            _fail(f"{name}: raised {type(exc).__name__}: {exc}")
            results.append({
                "test": name,
                "passed": False,
                "failures": [str(exc)],
                "latency_ms": -1,
            })

    # ── get_course_detail ──────────────────────────────────────────────────────
    check(
        "get_course_detail('Master of Data Science')",
        get_course_detail, ["Master of Data Science"], {},
        lambda r: [
            ("has name",          "name" in r),
            ("has faculty",       "faculty" in r),
            ("has career_outcomes", "career_outcomes" in r),
            ("has annual_fee_aud", "annual_fee_aud" in r),
        ],
    )
    check(
        "get_course_detail('zzz-no-such-course-xyz')",
        get_course_detail, ["zzz-no-such-course-xyz"], {},
        lambda r: [
            # Should return the closest match, not crash — pgvector always returns 1 row
            ("has name key",  "name" in r or "found" in r),
        ],
    )

    # ── search_courses ─────────────────────────────────────────────────────────
    check(
        "search_courses('software engineering')",
        search_courses, ["software engineering"], {},
        lambda r: [
            ("count >= 1",              r.get("count", 0) >= 1),
            ("has top_courses list",    isinstance(r.get("top_courses"), list)),
        ],
    )
    check(
        "search_courses('nursing', faculty='Health Sciences')",
        search_courses, ["nursing"], {"faculty": "Health Sciences"},
        lambda r: [
            ("count >= 1",  r.get("count", 0) >= 1),
        ],
    )
    check(
        "search_courses('business management')",
        search_courses, ["business management"], {},
        lambda r: [
            ("count >= 1",  r.get("count", 0) >= 1),
        ],
    )

    # ── recommend_courses ──────────────────────────────────────────────────────
    check(
        "recommend_courses(maths + problem solving)",
        recommend_courses, ["maths, problem solving", "sciences, analysis"], {},
        lambda r: [
            ("count >= 1",                   r.get("count", 0) >= 1),
            ("has top_recommendations list", isinstance(r.get("top_recommendations"), list)),
        ],
    )
    check(
        "recommend_courses(creative arts, Online mode)",
        recommend_courses, ["art, design, creativity", "visual arts"], {"study_mode_preference": "Online"},
        lambda r: [
            ("has count key",  "count" in r),
        ],
    )

    # ── search_events ──────────────────────────────────────────────────────────
    check(
        "search_events(no filter — next 30 days)",
        search_events, [], {},
        lambda r: [
            ("has count key",    "count" in r),
            ("has upcoming key", "upcoming" in r),
        ],
    )
    check(
        "search_events(type=CampusTour)",
        search_events, [], {"event_type": "CampusTour"},
        lambda r: [
            ("has count key",  "count" in r),
        ],
    )

    # ── search_knowledge ───────────────────────────────────────────────────────
    check(
        "search_knowledge('ATAR requirements for medicine')",
        search_knowledge, ["ATAR requirements for medicine"], {},
        lambda r: [
            ("has topic",               "topic" in r),
            ("has title",               "title" in r),
            ("has non-empty excerpt",   len(r.get("excerpt", "")) > 10),
        ],
    )
    check(
        "search_knowledge('HECS-HELP domestic student fees')",
        search_knowledge, ["HECS-HELP domestic student fees"], {},
        lambda r: [
            ("has topic",    "topic" in r),
            ("has excerpt",  "excerpt" in r),
        ],
    )
    check(
        "search_knowledge('student visa requirements international')",
        search_knowledge, ["student visa requirements international"], {},
        lambda r: [
            ("has topic",            "topic" in r),
            ("non-empty excerpt",    r.get("excerpt", "") != ""),
        ],
    )
    check(
        "search_knowledge('on-campus accommodation options')",
        search_knowledge, ["on-campus accommodation options"], {},
        lambda r: [
            ("has topic",  "topic" in r),
        ],
    )
    check(
        "search_knowledge('graduate salary career outcomes')",
        search_knowledge, ["graduate salary career outcomes"], {},
        lambda r: [
            ("has topic",  "topic" in r),
        ],
    )
    check(
        "search_knowledge('campus facilities library gym')",
        search_knowledge, ["campus facilities library gym sports"], {},
        lambda r: [
            ("has topic",  "topic" in r),
        ],
    )

    # ── search_scholarships ────────────────────────────────────────────────────
    check(
        "search_scholarships(general query — no type filter)",
        search_scholarships, ["scholarships available at Kingsford University"], {},
        lambda r: [
            ("count >= 1",               r.get("count", 0) >= 1),
            ("has top_scholarships list", isinstance(r.get("top_scholarships"), list)),
        ],
    )
    check(
        "search_scholarships(type=Merit)",
        search_scholarships, ["merit scholarship high achiever"], {"scholarship_type": "Merit"},
        lambda r: [
            ("count >= 1",  r.get("count", 0) >= 1),
        ],
    )
    check(
        "search_scholarships(type=Equity)",
        search_scholarships, ["equity support financial hardship"], {"scholarship_type": "Equity"},
        lambda r: [
            ("count >= 1",  r.get("count", 0) >= 1),
        ],
    )
    check(
        "search_scholarships(type=International) — exactly 1 by design",
        search_scholarships, ["international student scholarship funding"], {"scholarship_type": "International"},
        lambda r: [
            ("count == 1",  r.get("count", 0) == 1),
        ],
    )
    check(
        "search_scholarships(type=Faculty)",
        search_scholarships, ["faculty-specific award for engineering"], {"scholarship_type": "Faculty"},
        lambda r: [
            ("count >= 1",  r.get("count", 0) >= 1),
        ],
    )

    # ── book_campus_tour ───────────────────────────────────────────────────────
    check(
        "book_campus_tour(valid booking)",
        book_campus_tour, [], {
            "student_name": "Eval Runner",
            "email": "eval@waypoint.test",
            "preferred_date": "2026-04-10",
            "party_size": 2,
        },
        lambda r: [
            ("success=True",              r.get("success") is True),
            ("booking_id starts GT-",    r.get("booking_id", "").startswith("GT-")),
            ("has confirmation message", "message" in r),
        ],
    )
    check(
        "book_campus_tour(party_size=10 — out of range)",
        book_campus_tour, [], {
            "student_name": "Eval Runner",
            "email": "eval@waypoint.test",
            "preferred_date": "2026-04-10",
            "party_size": 10,
        },
        lambda r: [
            ("success=False",  r.get("success") is False),
            ("has error key",  "error" in r),
        ],
    )
    check(
        "book_campus_tour(bad date format)",
        book_campus_tour, [], {
            "student_name": "Eval Runner",
            "email": "eval@waypoint.test",
            "preferred_date": "not-a-date",
            "party_size": 1,
        },
        lambda r: [
            ("success=False",  r.get("success") is False),
        ],
    )

    return results


# ── Layer 2: Tool routing via Gemini text API ──────────────────────────────────

# Clara's system prompt adapted for text-mode routing tests
_ROUTING_SYSTEM = """
You are Clara, Kingsford University's AI course counsellor.
For every student query, decide whether to call a tool or respond conversationally.

Tool routing rules (follow exactly):
- Student asks for more detail about a specific course by name      → call get_course_detail
- Student asks about courses, programs, or fields of study          → call search_courses
- Student wants personalised recommendations based on interests      → call recommend_courses
- Student asks about upcoming events, open days, info sessions       → call search_events
- Student wants to book a campus tour                                → call book_campus_tour
- Student asks about scholarships, bursaries, or financial support   → call search_scholarships
- Student asks about admissions, ATAR, HECS-HELP, fees, visa,
  campus life, accommodation, transport, facilities, or careers       → call search_knowledge
- Greetings, thanks, vague chat, "what can you do" questions         → NO tool; respond conversationally
""".strip()


def _build_tool_declarations():
    import google.genai.types as t
    return t.Tool(function_declarations=[
        t.FunctionDeclaration(
            name="get_course_detail",
            description="Get full details for a specific course the student already knows about by name.",
            parameters=t.Schema(type="OBJECT", properties={
                "course_name": t.Schema(type="STRING"),
            }, required=["course_name"]),
        ),
        t.FunctionDeclaration(
            name="search_courses",
            description="Search Kingsford University courses by natural language query.",
            parameters=t.Schema(type="OBJECT", properties={
                "query":   t.Schema(type="STRING"),
                "faculty": t.Schema(type="STRING"),
            }, required=["query"]),
        ),
        t.FunctionDeclaration(
            name="recommend_courses",
            description="Recommend courses based on student interests, strengths, and study mode.",
            parameters=t.Schema(type="OBJECT", properties={
                "interests":              t.Schema(type="STRING"),
                "strengths":              t.Schema(type="STRING"),
                "study_mode_preference":  t.Schema(type="STRING"),
            }, required=["interests", "strengths"]),
        ),
        t.FunctionDeclaration(
            name="search_events",
            description="Search upcoming university events (open days, info sessions, campus tours).",
            parameters=t.Schema(type="OBJECT", properties={
                "event_type":  t.Schema(type="STRING"),
                "date_range":  t.Schema(type="STRING"),
            }),
        ),
        t.FunctionDeclaration(
            name="book_campus_tour",
            description="Book a campus tour for a student.",
            parameters=t.Schema(type="OBJECT", properties={
                "student_name":   t.Schema(type="STRING"),
                "email":          t.Schema(type="STRING"),
                "preferred_date": t.Schema(type="STRING"),
                "party_size":     t.Schema(type="INTEGER"),
            }, required=["student_name", "preferred_date"]),
        ),
        t.FunctionDeclaration(
            name="search_knowledge",
            description=(
                "Search knowledge base for admissions, ATAR, HECS-HELP, fees, visa, "
                "campus life, accommodation, facilities, or career outcomes."
            ),
            parameters=t.Schema(type="OBJECT", properties={
                "query": t.Schema(type="STRING"),
            }, required=["query"]),
        ),
        t.FunctionDeclaration(
            name="search_scholarships",
            description=(
                "Search scholarships, bursaries, and financial awards. "
                "Optional type filter: Merit, Equity, International, Faculty."
            ),
            parameters=t.Schema(type="OBJECT", properties={
                "query":            t.Schema(type="STRING"),
                "scholarship_type": t.Schema(type="STRING"),
            }, required=["query"]),
        ),
    ])


def run_layer2(queries_path: str) -> list[dict]:
    _head("Layer 2: Tool Routing (Gemini Text API)")

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        _skip("GOOGLE_API_KEY not set — skipping Layer 2")
        return []

    import google.genai as genai
    import google.genai.types as t

    client = genai.Client(api_key=api_key)
    tool_decls = _build_tool_declarations()

    with open(queries_path) as f:
        test_cases = [tc for tc in json.load(f) if tc.get("layer") == 2]

    results: list[dict] = []

    for tc in test_cases:
        query        = tc["query"]
        expected     = tc.get("expected_tool")
        test_id      = tc.get("id", "?")
        description  = tc.get("description", query[:40])

        t0 = time.monotonic()
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=query,
                config=t.GenerateContentConfig(
                    system_instruction=_ROUTING_SYSTEM,
                    tools=[tool_decls],
                    temperature=0,
                ),
            )
            latency_ms = round((time.monotonic() - t0) * 1000)

            # Extract function call if the model chose one
            called_tool: Optional[str] = None
            candidate = response.candidates[0] if response.candidates else None
            if candidate and candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        called_tool = part.function_call.name
                        break

            passed = (called_tool == expected)
            label  = f"[{test_id}] {description[:50]}"
            detail = f"expected={expected!r}, got={called_tool!r}  ({latency_ms}ms)"

            if passed:
                _ok(f"{label}  →  {detail}")
            else:
                _fail(f"{label}  →  {detail}")

            results.append({
                "id":            test_id,
                "query":         query,
                "expected_tool": expected,
                "actual_tool":   called_tool,
                "passed":        passed,
                "latency_ms":    latency_ms,
            })

        except Exception as exc:
            _fail(f"[{test_id}] {description[:50]} raised {type(exc).__name__}: {exc}")
            results.append({
                "id":            test_id,
                "query":         query,
                "expected_tool": expected,
                "actual_tool":   None,
                "passed":        False,
                "latency_ms":    -1,
            })

    return results


# ── Layer 2b: Multi-turn conversation routing ──────────────────────────────────

# Synthetic model stub responses injected into history after each tool call.
# These simulate Clara's spoken summary so the next turn has realistic context.
_TURN_STUBS: dict[Optional[str], str] = {
    "get_course_detail":   "I've pulled up the full details for that course, including the description and career outcomes. Is there anything else you'd like to explore?",
    "search_courses":      "I found some matching courses for you — you can see them on the card. Would you like more detail on any of them?",
    "recommend_courses":   "Based on your interests, here are some courses that would suit you well. Would you like more information on any of them?",
    "search_events":       "I found some upcoming events that might interest you. Would you like to attend or book a tour?",
    "book_campus_tour":    "Your campus tour has been booked! Is there anything else I can help you with?",
    "search_knowledge":    "Here's some information about that. Is there anything specific you'd like to know more about?",
    "search_scholarships": "I found some scholarships you may be eligible for. Would you like to know more about any of them?",
    None:                  "Happy to help! What would you like to know?",
}


def run_layer2b(queries_path: str) -> list[dict]:
    _head("Layer 2b: Multi-Turn Conversation Routing (Gemini Text API)")

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        _skip("GOOGLE_API_KEY not set — skipping Layer 2b")
        return []

    import google.genai as genai
    import google.genai.types as t

    client = genai.Client(api_key=api_key)
    tool_decls = _build_tool_declarations()

    with open(queries_path) as f:
        conversations = [tc for tc in json.load(f) if tc.get("layer") == "2b"]

    results: list[dict] = []

    for conv in conversations:
        conv_id   = conv.get("id", "?")
        conv_desc = conv.get("description", "")
        turns     = conv.get("turns", [])

        print(f"\n  {BOLD}[{conv_id}]{RESET} {conv_desc}")

        # Conversation history accumulated across turns
        history: list = []
        conv_passed  = True
        turn_results = []

        for i, turn in enumerate(turns):
            user_text    = turn["user"]
            expected     = turn.get("expected_tool")
            turn_label   = f"  Turn {i+1}"

            # Build contents: history so far + this user message
            contents = history + [t.Content(parts=[t.Part(text=user_text)], role="user")]

            t0 = time.monotonic()
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=t.GenerateContentConfig(
                        system_instruction=_ROUTING_SYSTEM,
                        tools=[tool_decls],
                        temperature=0,
                    ),
                )
                latency_ms = round((time.monotonic() - t0) * 1000)

                called_tool: Optional[str] = None
                candidate = response.candidates[0] if response.candidates else None
                if candidate and candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            called_tool = part.function_call.name
                            break

                passed = (called_tool == expected)
                if not passed:
                    conv_passed = False

                detail = f"expected={expected!r}, got={called_tool!r}  ({latency_ms}ms)"
                if passed:
                    _ok(f"{turn_label}: \"{user_text[:55]}\"  →  {detail}")
                else:
                    _fail(f"{turn_label}: \"{user_text[:55]}\"  →  {detail}")

                turn_results.append({
                    "turn":          i + 1,
                    "user":          user_text,
                    "expected_tool": expected,
                    "actual_tool":   called_tool,
                    "passed":        passed,
                    "latency_ms":    latency_ms,
                })

                # Advance history: user message + synthetic model response
                history.append(t.Content(parts=[t.Part(text=user_text)], role="user"))
                stub = _TURN_STUBS.get(called_tool, _TURN_STUBS[None])
                history.append(t.Content(parts=[t.Part(text=stub)], role="model"))

            except Exception as exc:
                _fail(f"{turn_label}: raised {type(exc).__name__}: {exc}")
                turn_results.append({
                    "turn":          i + 1,
                    "user":          user_text,
                    "expected_tool": expected,
                    "actual_tool":   None,
                    "passed":        False,
                    "latency_ms":    -1,
                })
                conv_passed = False
                # Advance history with stub so remaining turns still run
                history.append(t.Content(parts=[t.Part(text=user_text)], role="user"))
                history.append(t.Content(parts=[t.Part(text=_TURN_STUBS[None])], role="model"))

        results.append({
            "id":          conv_id,
            "description": conv_desc,
            "passed":      conv_passed,
            "turns":       turn_results,
        })

    return results


# ── Report ─────────────────────────────────────────────────────────────────────

def print_report(layer1: list[dict], layer2: list[dict], layer2b: list[dict] = []) -> bool:
    _head("═══ Evaluation Report ═══")

    def _avg_latency(results):
        valid = [r["latency_ms"] for r in results if r.get("latency_ms", -1) > 0]
        return round(sum(valid) / len(valid)) if valid else 0

    # Flatten layer2b turn results for counting
    layer2b_turns = [t for conv in layer2b for t in conv.get("turns", [])]

    all_results = layer1 + layer2 + layer2b_turns
    total  = len(all_results)
    passed = sum(1 for r in all_results if r["passed"])

    if layer1:
        l1_pass = sum(1 for r in layer1 if r["passed"])
        print(f"  Layer 1  (Tool Correctness):     {l1_pass}/{len(layer1)} passed  "
              f"avg {_avg_latency(layer1)}ms/call")

    if layer2:
        l2_pass = sum(1 for r in layer2 if r["passed"])
        print(f"  Layer 2  (Single-Turn Routing):  {l2_pass}/{len(layer2)} passed  "
              f"avg {_avg_latency(layer2)}ms/query")

    if layer2b:
        l2b_turn_pass = sum(1 for t in layer2b_turns if t["passed"])
        l2b_conv_pass = sum(1 for c in layer2b if c["passed"])
        print(f"  Layer 2b (Multi-Turn Routing):   {l2b_turn_pass}/{len(layer2b_turns)} turns passed  "
              f"({l2b_conv_pass}/{len(layer2b)} full conversations)  "
              f"avg {_avg_latency(layer2b_turns)}ms/turn")

    pct = (100 * passed // total) if total else 0
    colour = GREEN if pct == 100 else (YELLOW if pct >= 80 else RED)
    print(f"\n  {BOLD}{colour}Overall: {passed}/{total} passed ({pct}%){RESET}")

    failures = [r for r in all_results if not r["passed"]]
    if failures:
        print(f"\n  {RED}Failures:{RESET}")
        for r in failures:
            label = r.get("user") or r.get("query") or r.get("test") or "?"
            print(f"    - {label[:72]}")

    # Write JSON report
    report = {
        "summary": {"total": total, "passed": passed, "pct": pct},
        "layer1":   layer1,
        "layer2":   layer2,
        "layer2b":  layer2b,
    }
    report_path = Path(__file__).parent / "eval_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Full report → {report_path.name}")

    return passed == total


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Waypoint evaluation suite")
    parser.add_argument("--layer1-only", action="store_true",
                        help="Only run direct tool tests (no Gemini API needed)")
    parser.add_argument("--layer2-only", action="store_true",
                        help="Only run single-turn routing tests (no DATABASE_URL needed)")
    parser.add_argument("--layer2b-only", action="store_true",
                        help="Only run multi-turn routing tests (no DATABASE_URL needed)")
    parser.add_argument("--no-multiturn", action="store_true",
                        help="Skip Layer 2b multi-turn tests (faster run)")
    parser.add_argument("--queries", default="data/eval_queries.json",
                        help="Path to eval_queries.json (default: data/eval_queries.json)")
    args = parser.parse_args()

    layer1_results:  list[dict] = []
    layer2_results:  list[dict] = []
    layer2b_results: list[dict] = []

    run_db    = not args.layer2_only and not args.layer2b_only
    run_l2    = not args.layer1_only and not args.layer2b_only
    run_l2b   = not args.layer1_only and not args.layer2_only and not args.no_multiturn

    if run_db:
        layer1_results = run_layer1()

    if run_l2:
        layer2_results = run_layer2(args.queries)

    if run_l2b:
        layer2b_results = run_layer2b(args.queries)

    ok = print_report(layer1_results, layer2_results, layer2b_results)
    sys.exit(0 if ok else 1)
