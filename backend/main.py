"""
Waypoint FastAPI app — WebSocket bridge using Google ADK Runner.run_live().

Architecture:
  - Per-connection InMemorySessionService + Runner (avoids event-loop conflicts)
  - Audio pipeline: Runner.run_live() + LiveRequestQueue
  - Tool dispatch:  ADK handles automatically (tools registered on sage Agent)
  - display_data:   side-channel via registered async callbacks

Browser audio protocol:
  Browser → Server  binary : raw PCM 16-bit LE, 16 000 Hz, mono
  Browser → Server  text   : JSON {"type": "text", "content": "..."}
  Server  → Browser binary : raw PCM audio from model (24 000 Hz)
  Server  → Browser text   : JSON one of:
      {"type": "transcript", "role": "user"|"agent", "text": "..."}
      {"type": "card",       "card_type": "...", "data": {...}, "spoken_summary": "..."}
      {"type": "turn_complete"}
      {"type": "error",      "message": "..."}
"""
import asyncio
import json
import logging
import os
import pathlib
import sys

from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import google.genai.types as types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue

from agent import clara, MODEL
from db import init_pool, close_pool
from tools import register_display_callback, unregister_display_callback

# ── ADK bug fix: GeminiLlmConnection.send_realtime uses media= (→ mediaChunks
# wire format, deprecated) instead of audio= (→ audio wire format required by
# native audio VAD). Monkey-patch to use the correct wire path.
from google.adk.models.gemini_llm_connection import GeminiLlmConnection

_patch_call_count = 0

async def _patched_send_realtime(self, input):
    global _patch_call_count
    _patch_call_count += 1
    if _patch_call_count == 1:
        log.info("PATCH CONFIRMED: send_realtime called (audio= path active)")
    if isinstance(input, types.Blob):
        await self._gemini_session.send_realtime_input(audio=input)
    elif isinstance(input, types.ActivityStart):
        await self._gemini_session.send_realtime_input(activity_start=input)
    elif isinstance(input, types.ActivityEnd):
        await self._gemini_session.send_realtime_input(activity_end=input)
    else:
        raise ValueError(f"Unsupported realtime input type: {type(input)}")

GeminiLlmConnection.send_realtime = _patched_send_realtime
log_patch = logging.getLogger("waypoint")
log_patch.info("GeminiLlmConnection.send_realtime patched: media= → audio=")

# ── Config ────────────────────────────────────────────────────────────────────
APP_NAME   = "waypoint"
STATIC_DIR = pathlib.Path(__file__).parent.parent / "frontend"
log        = logging.getLogger("waypoint")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ── App lifecycle ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    log.info("DB pool ready")
    yield
    await close_pool()
    log.info("DB pool closed")

app = FastAPI(lifespan=lifespan)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000 http://127.0.0.1:8000").split()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── HTTP routes ───────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}

# ── WebSocket bridge ──────────────────────────────────────────────────────────
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    log.info("WS connected: %s", client_id)

    loop = asyncio.get_event_loop()

    # display_data side-channel — cards → browser via same WebSocket
    async def send_card(payload: dict):
        try:
            await websocket.send_text(json.dumps(payload))
        except Exception:
            pass

    register_display_callback(client_id, loop, send_card)

    # Per-connection session service + runner
    # (module-level singletons conflict with FastAPI's async event loop)
    session_service = InMemorySessionService()
    runner = Runner(agent=clara, app_name=APP_NAME, session_service=session_service)

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=client_id,
    )
    log.info("ADK session created: %s", session.id)

    live_request_queue = LiveRequestQueue()

    # Note: Using string "AUDIO" for response_modalities. Even though it triggers
    # a Pydantic warning, the ADK internals currently require the string value
    # for membership checks (e.g. 'AUDIO' in response_modalities).
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        context_window_compression=types.ContextWindowCompressionConfig(
            sliding_window=types.SlidingWindow(target_tokens=15000),
        ),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
            ),
            language_code="en-US",
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )

    try:
        async def receive_from_browser():
            chunk_count = 0
            try:
                while True:
                    message = await websocket.receive()
                    if message["type"] == "websocket.disconnect":
                        break
                    if "bytes" in message and message["bytes"]:
                        chunk_count += 1
                        if chunk_count % 100 == 0:
                            log.info("Audio chunk #%d (%d bytes)", chunk_count, len(message["bytes"]))
                        live_request_queue.send_realtime(
                            types.Blob(
                                data=message["bytes"],
                                mime_type="audio/pcm;rate=16000",
                            )
                        )
                    elif "text" in message and message["text"]:
                        msg = json.loads(message["text"])
                        if msg.get("type") == "text":
                            log.info("Text input: %s", msg["content"][:60])
                            live_request_queue.send_content(
                                types.Content(parts=[types.Part(text=msg["content"])])
                            )
                        elif msg.get("type") == "audio_stop":
                            log.info("Audio stream stopped (mic off)")
                            chunk_count = 0
            except (WebSocketDisconnect, RuntimeError):
                pass
            finally:
                live_request_queue.close()

        async def send_to_browser():
            log.info("Starting ADK run_live for session %s", session.id)
            try:
                async for event in runner.run_live(
                    user_id=client_id,
                    session_id=session.id,
                    live_request_queue=live_request_queue,
                    run_config=run_config,
                ):
                    has_content = bool(event.content and event.content.parts)
                    in_text = getattr(getattr(event, "input_transcription", None), "text", None)
                    out_text = getattr(getattr(event, "output_transcription", None), "text", None)
                    is_turn_complete = getattr(event, "turn_complete", False)
                    # Only log events with actual transcription, text output, or turn complete indicators
                    if in_text or out_text or is_turn_complete or (has_content and not getattr(event, "partial", False)):
                        log.info("ADK event: author=%s turn_complete=%s partial=%s has_content=%s in_tx=%r out_tx=%r",
                                 getattr(event, "author", "?"),
                                 is_turn_complete,
                                 getattr(event, "partial", False),
                                 has_content,
                                 in_text,
                                 out_text,
                        )
                    # Audio output
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                                await websocket.send_bytes(part.inline_data.data)

                    # Transcriptions
                    if event.output_transcription:
                        text = (getattr(event.output_transcription, "text", "") or "").strip()
                        if text and not text.startswith("**"):
                            await websocket.send_text(json.dumps({
                                "type": "transcript", "role": "agent", "text": text,
                            }))
                    if event.input_transcription:
                        text = (getattr(event.input_transcription, "text", "") or "").strip()
                        if text:
                            is_final = (event.partial is False)
                            await websocket.send_text(json.dumps({
                                "type": "transcript", "role": "user", "text": text,
                                "final": is_final,
                            }))

                    # Turn complete
                    if event.turn_complete:
                        await websocket.send_text(json.dumps({"type": "turn_complete"}))

            except Exception as e:
                # If the error is just a 1000 OK (e.g. model closing or reloader forcing shutdown),
                # log it quietly and exit the loop.
                if "1000" in str(e):
                    log.info("Gemini Live connection closed normally (1000 OK).")
                else:
                    log.error("send_to_browser error: %s", e)
                    try:
                        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
                    except Exception:
                        pass

        # Use wait FIRST_COMPLETED so that if the model disconnects (send_to_browser ends),
        # the browser task is cancelled and the WebSocket closes, preventing "zombie" UI states.
        done, pending = await asyncio.wait(
            [asyncio.create_task(receive_from_browser()), asyncio.create_task(send_to_browser())],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    except Exception as e:
        log.error("WS session error: %s", e)
    finally:
        unregister_display_callback(client_id)
        log.info("WS disconnected: %s", client_id)
