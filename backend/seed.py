"""
Seed script: applies schema.sql, inserts seed.sql, then generates embeddings
for all courses using text-embedding-004 via the Gemini API.

Run: python backend/seed.py
"""
import asyncio
import os
import pathlib

import asyncpg
from dotenv import load_dotenv

load_dotenv()

ROOT = pathlib.Path(__file__).parent.parent
SCHEMA = ROOT / "data" / "schema.sql"
SEED   = ROOT / "data" / "seed.sql"


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using text-embedding-004 via google-genai."""
    import google.genai as genai
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    import google.genai.types as genai_types
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=genai_types.EmbedContentConfig(output_dimensionality=1536),
    )
    return [e.values for e in result.embeddings]


async def main():
    dsn = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(dsn)

    print("Applying schema …")
    await conn.execute(SCHEMA.read_text())

    print("Inserting seed data …")
    await conn.execute("TRUNCATE courses, events, tour_bookings RESTART IDENTITY CASCADE")
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
            emb_str = "[" + ",".join(str(v) for v in emb) + "]"
            await conn.execute(
                "UPDATE courses SET embedding = $1::vector WHERE id = $2",
                emb_str, row["id"]
            )
        print(f"  Embedded {len(rows)} courses.")
    else:
        print("  Embeddings already present, skipping.")

    count = await conn.fetchval("SELECT COUNT(*) FROM courses")
    events = await conn.fetchval("SELECT COUNT(*) FROM events")
    print(f"\nDatabase ready: {count} courses, {events} events.")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
