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

# ── Gemini ADK Monkey-Patching ───────────────────────────────────────────────
# ADK's send_content uses the deprecated send() method which fails to correctly
# format tool responses (missing camelCase conversion). We patch both methods:
#   send_content  → routes function responses via send_tool_response()
#   send_realtime → uses audio= wire path required for native audio VAD
from google.adk.models.gemini_llm_connection import GeminiLlmConnection

async def _patched_send_content(self, content: types.Content):
    if not content.parts:
        return
    if content.parts[0].function_response:
        # Build the tool_response JSON manually to avoid send_tool_response()'s
        # convert_keys=True recursively camelCasing our tool result payload keys,
        # which can cause the native audio model to crash with 1011.
        function_responses = [p.function_response for p in content.parts if p.function_response]
        if function_responses:
            payload = json.dumps({
                "tool_response": {
                    "functionResponses": [
                        {"id": fr.id, "name": fr.name, "response": fr.response}
                        for fr in function_responses
                    ]
                }
            })
            await self._gemini_session._ws.send(payload)
    else:
        await self._gemini_session.send_client_content(turns=[content], turn_complete=True)

async def _patched_send_realtime(self, input):
    if isinstance(input, types.Blob):
        await self._gemini_session.send_realtime_input(audio=input)
    elif isinstance(input, types.ActivityStart):
        await self._gemini_session.send_realtime_input(activity_start=input)
    elif isinstance(input, types.ActivityEnd):
        await self._gemini_session.send_realtime_input(activity_end=input)
    else:
        raise ValueError(f"Unsupported realtime input type: {type(input)}")

GeminiLlmConnection.send_content = _patched_send_content
GeminiLlmConnection.send_realtime = _patched_send_realtime

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

    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=[types.Modality.AUDIO],
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
            try:
                while True:
                    message = await websocket.receive()
                    if message["type"] == "websocket.disconnect":
                        break
                    if "bytes" in message and message["bytes"]:
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
                            log.info("Mic off")
            except (WebSocketDisconnect, RuntimeError):
                pass
            finally:
                live_request_queue.close()

        async def run_live_loop():
            """Process ADK events from a single run_live session."""
            async for event in runner.run_live(
                user_id=client_id,
                session_id=session.id,
                live_request_queue=live_request_queue,
                run_config=run_config,
            ):
                in_text = getattr(getattr(event, "input_transcription", None), "text", None)
                out_text = getattr(getattr(event, "output_transcription", None), "text", None)
                is_turn_complete = getattr(event, "turn_complete", False)
                if in_text and not getattr(event, "partial", True):
                    log.info("User: %s", in_text)
                if out_text and not getattr(event, "partial", True):
                    log.info("Clara: %s", out_text)
                if is_turn_complete:
                    log.info("Turn complete")
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

        async def send_to_browser():
            log.info("Starting ADK run_live for session %s", session.id)
            MAX_RETRIES = 3
            for attempt in range(MAX_RETRIES):
                try:
                    await run_live_loop()
                    break  # clean exit
                except Exception as e:
                    err_str = str(e)
                    if "1000" in err_str:
                        log.info("Gemini Live connection closed normally.")
                        break
                    elif ("1011" in err_str or "1008" in err_str) and attempt < MAX_RETRIES - 1:
                        log.warning("Gemini session dropped (%s), reconnecting (attempt %d/%d)…",
                                    err_str[:40],
                                    attempt + 2, MAX_RETRIES)
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        log.error("send_to_browser error: %s", e)
                        try:
                            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
                        except Exception:
                            pass
                        break

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
