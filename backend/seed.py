"""
Seed script: applies schema.sql, inserts seed.sql, then generates embeddings
for courses, knowledge_docs (chunked from markdown files), and scholarships.

Run: python backend/seed.py
"""
import asyncio
import os
import pathlib
import re

import asyncpg
from dotenv import load_dotenv

load_dotenv()

ROOT       = pathlib.Path(__file__).parent.parent
SCHEMA     = ROOT / "data" / "schema.sql"
SEED       = ROOT / "data" / "seed.sql"
KNOWLEDGE  = ROOT / "data" / "knowledge"

TOPIC_MAP = {
    "admissions":             "admissions",
    "fees_and_scholarships":  "fees",
    "campus_life":            "campus-life",
    "international_students": "international",
    "facilities":             "facilities",
    "career_outcomes":        "careers",
}


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using gemini-embedding-001 via google-genai."""
    import google.genai as genai
    import google.genai.types as genai_types
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=genai_types.EmbedContentConfig(output_dimensionality=1536),
    )
    return [e.values for e in result.embeddings]


def _emb_str(values) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def chunk_markdown(path: pathlib.Path) -> list[dict]:
    """
    Split a markdown file into sections by ## headings.
    Returns list of {title, content} dicts.
    Each chunk = heading + its body text, trimmed of whitespace.
    """
    text = path.read_text(encoding="utf-8")
    # Split on ## headings (keep the heading in each chunk)
    parts = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    chunks = []
    for part in parts:
        part = part.strip()
        # Only keep ## sections — skip the H1 file header (no real content)
        if not part or not part.startswith("## "):
            continue
        lines = part.splitlines()
        title = lines[0].lstrip("#").strip() if lines else path.stem
        content = "\n".join(lines[1:]).strip() if len(lines) > 1 else part
        # Skip near-empty sections (e.g. just a heading with no body)
        if len(content) < 30:
            continue
        chunks.append({"title": title, "content": part})  # store full chunk as content
    return chunks


async def seed_knowledge_docs(conn: asyncpg.Connection) -> int:
    """Read markdown files, chunk by section, embed, and insert into knowledge_docs."""
    total = 0
    for md_file in sorted(KNOWLEDGE.glob("*.md")):
        stem = md_file.stem
        topic = TOPIC_MAP.get(stem, stem)
        chunks = chunk_markdown(md_file)
        if not chunks:
            print(f"  [knowledge] {md_file.name}: no chunks found, skipping.")
            continue

        texts = [f"{c['title']}\n\n{c['content']}" for c in chunks]
        embeddings = await embed_texts(texts)

        for chunk, emb in zip(chunks, embeddings):
            emb_str = _emb_str(emb)
            await conn.execute(
                """
                INSERT INTO knowledge_docs (topic, title, content, embedding)
                VALUES ($1, $2, $3, $4::vector)
                """,
                topic, chunk["title"], chunk["content"], emb_str,
            )
        total += len(chunks)
        print(f"  [knowledge] {md_file.name}: {len(chunks)} chunks embedded.")
    return total


async def seed_scholarships(conn: asyncpg.Connection) -> int:
    """Generate embeddings for all scholarship rows and update in place."""
    rows = await conn.fetch(
        "SELECT id, name, type, eligibility, description FROM scholarships WHERE embedding IS NULL"
    )
    if not rows:
        print("  [scholarships] Embeddings already present, skipping.")
        return 0

    texts = [
        f"{r['name']} | {r['type']} scholarship | Eligibility: {r['eligibility']} | {r['description']}"
        for r in rows
    ]
    embeddings = await embed_texts(texts)

    for row, emb in zip(rows, embeddings):
        emb_str = _emb_str(emb)
        await conn.execute(
            "UPDATE scholarships SET embedding = $1::vector WHERE id = $2",
            emb_str, row["id"],
        )
    print(f"  [scholarships] Embedded {len(rows)} scholarships.")
    return len(rows)


async def main():
    dsn = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(dsn)

    print("Applying schema …")
    await conn.execute(SCHEMA.read_text())

    print("Inserting seed data …")
    await conn.execute(
        "TRUNCATE courses, events, tour_bookings, knowledge_docs, scholarships RESTART IDENTITY CASCADE"
    )
    await conn.execute(SEED.read_text())

    print("Generating course embeddings …")
    rows = await conn.fetch(
        "SELECT id, name, faculty, description, career_outcomes FROM courses WHERE embedding IS NULL"
    )
    if rows:
        texts = [
            f"{r['name']} | {r['faculty']} | {r['description']} | Careers: {r['career_outcomes']}"
            for r in rows
        ]
        embeddings = await embed_texts(texts)
        for row, emb in zip(rows, embeddings):
            emb_str = _emb_str(emb)
            await conn.execute(
                "UPDATE courses SET embedding = $1::vector WHERE id = $2",
                emb_str, row["id"],
            )
        print(f"  [courses] Embedded {len(rows)} courses.")
    else:
        print("  [courses] Embeddings already present, skipping.")

    print("Generating knowledge doc embeddings …")
    n_chunks = await seed_knowledge_docs(conn)

    print("Generating scholarship embeddings …")
    await seed_scholarships(conn)

    course_count = await conn.fetchval("SELECT COUNT(*) FROM courses")
    event_count  = await conn.fetchval("SELECT COUNT(*) FROM events")
    doc_count    = await conn.fetchval("SELECT COUNT(*) FROM knowledge_docs")
    schol_count  = await conn.fetchval("SELECT COUNT(*) FROM scholarships")

    print(f"\nDatabase ready:")
    print(f"  {course_count} courses")
    print(f"  {event_count} events")
    print(f"  {doc_count} knowledge doc chunks ({n_chunks} embedded this run)")
    print(f"  {schol_count} scholarships")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
