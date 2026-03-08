"""
Day 1 spike: confirm ADK audio round-trip with gemini-live-2.5-flash.

Sends a text turn to the live session and prints any transcript / audio events back.
Run: python spike_audio.py

Requires GOOGLE_API_KEY in .env (or env var).
"""
import asyncio
import os

from dotenv import load_dotenv
load_dotenv()

import google.genai.types as genai_types
from google.genai.types import Modality
from google.adk import Agent, Runner
from google.adk.agents.live_request_queue import LiveRequest, LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions import InMemorySessionService

# ── Config ────────────────────────────────────────────────────────────────────
MODEL = os.getenv("MODEL_NAME", "gemini-2.5-flash-native-audio-latest")
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY in .env or environment")

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"  # use API key path, not Vertex

# ── Minimal agent ─────────────────────────────────────────────────────────────
clara = Agent(
    name="clara",
    model=MODEL,
    description="Kingsford University course counsellor",
    instruction=(
        "You are Clara, a friendly course counsellor for Kingsford University "
        "in Melbourne, Australia. Keep all spoken replies under 50 words."
    ),
)

# ── Run ───────────────────────────────────────────────────────────────────────
async def main():
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="waypoint", user_id="spike_user"
    )

    runner = Runner(
        agent=clara,
        app_name="waypoint",
        session_service=session_service,
    )

    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=[Modality.AUDIO],
        output_audio_transcription=genai_types.AudioTranscriptionConfig(),
    )

    request_queue = LiveRequestQueue()

    print(f"[spike] Connecting to {MODEL} …")

    async def feed_input():
        """Send a single text turn then close."""
        await asyncio.sleep(0.5)  # let the session handshake settle
        msg = "Hi Clara! What kinds of courses does Kingsford University offer?"
        print(f"[user]  {msg}")
        request_queue.send_content(
            content=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=msg)],
            )
        )
        await asyncio.sleep(8)   # wait for response before closing
        request_queue.close()

    async def read_events():
        """Collect and print events from the live session."""
        try:
            async for event in runner.run_live(
                session_id=session.id,
                user_id="spike_user",
                live_request_queue=request_queue,
                run_config=run_config,
            ):
                # Print any text content
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            role = getattr(event.content, "role", None) or "agent"
                            print(f"[{role}]   {part.text}")
                # Print transcript from audio (if present)
                if hasattr(event, "server_content") and event.server_content:
                    sc = event.server_content
                    if hasattr(sc, "output_transcription") and sc.output_transcription:
                        print(f"[transcript] {sc.output_transcription.text}")
                # Print turn-complete marker
                if getattr(event, "turn_complete", False):
                    print("[spike] turn_complete ✓")
        except Exception as e:
            # Code 1000 = normal WebSocket close after queue.close() — not a real error
            if "1000" in str(e):
                print("[spike] Connection closed normally (1000 OK) ✓")
            else:
                raise

    await asyncio.gather(feed_input(), read_events())
    print("[spike] Done.")


if __name__ == "__main__":
    asyncio.run(main())
