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
import re
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
            # We use an ID mapping to ensure the tool response IDs strictly match 
            # the most recent function calls from the model.
            payload = json.dumps({
                "tool_response": {
                    "functionResponses": [
                        {"id": fr.id, "name": fr.name, "response": fr.response}
                        for fr in function_responses
                    ]
                }
            })
            log.info("Sending tool response (%d bytes): %s", len(payload), payload[:300])
            await self._gemini_session._ws.send(payload)
            log.info("Tool response sent successfully")
    else:
        await self._gemini_session.send(
            input=types.LiveClientContent(
                turns=[content],
                turn_complete=True,
            )
        )

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
log        = logging.getLogger(__name__)

HIDDEN_GREETING_PROMPT = "(System: The student has just arrived. Please greet them warmly as Clara, the Kingsford University course counsellor. Ask how you can help them explore courses or events today. Keep it brief and friendly.)"
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s.%(msecs)03d %(levelname)s  %(message)s",
    datefmt="%H:%M:%S"
)

# Global singletons for session management
session_service = InMemorySessionService()
runner = Runner(agent=clara, app_name=APP_NAME, session_service=session_service)

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

def _sanitize_session_events(events):
    """Sanitize session events for safe replay on reconnect.

    Removes:
    - Audio inline_data parts (native audio models reject these in history)
    - Function call / function response parts (can cause 1007 if malformed
      from a crashed turn)
    - Empty content objects left after filtering
    """
    for event in events:
        if event.content and event.content.parts:
            event.content.parts = [
                p for p in event.content.parts
                if not (p.inline_data and p.inline_data.mime_type
                        and p.inline_data.mime_type.startswith("audio/"))
                and not p.function_call
                and not p.function_response
            ]

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

    # Use a consistent session per client_id to preserve history
    # if the WebSocket reconnects.
    try:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=client_id,
            session_id=client_id # Use client_id as session_id for persistence
        )
        if not session:
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=client_id,
                session_id=client_id
            )
            log.info("ADK session created: %s", session.id)
        else:
            log.info("ADK session resumed: %s (history: %d events)",
                     session.id, len(session.events))
            _sanitize_session_events(session.events)

    except Exception as e:
        # Fallback to fresh session if retrieval fails
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=client_id,
        )
        log.warning("ADK session fresh start (retrieval failed: %s): %s", e, session.id)

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
        context_window_compression=None,
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
            """Process ADK events with a retry loop for transient errors and session limits."""
            nonlocal session
            max_attempts = 10
            consecutive_1007 = 0
            for attempt in range(1, max_attempts + 1):
                try:
                    if attempt > 1:
                        log.info("Retry attempt %d/%d after session interruption...", attempt, max_attempts)
                        await asyncio.sleep(2)

                        # Drain stale audio from the queue
                        cleared = 0
                        while not live_request_queue._queue.empty():
                            try:
                                live_request_queue._queue.get_nowait()
                                cleared += 1
                            except asyncio.QueueEmpty:
                                break
                        log.info("Drained %d stale items from live_request_queue before retry.", cleared)

                        # If we've hit 2+ consecutive 1007s, the session history is
                        # irrecoverably corrupted. Start fresh.
                        if consecutive_1007 >= 2:
                            log.warning("Session history corrupted (2+ consecutive 1007s). Creating fresh session.")
                            session = await session_service.create_session(
                                app_name=APP_NAME,
                                user_id=client_id,
                                session_id=f"{client_id}-{attempt}",
                            )
                            consecutive_1007 = 0
                        else:
                            # Sanitize session events (audio, function calls/responses)
                            _sanitize_session_events(session.events)
                    
                    # Cumulative transcript buffers (matching Vanina/raw SDK pattern):
                    # ADK yields deltas; we accumulate and send the full buffer each time.
                    user_tx_buf = ""
                    agent_tx_buf = ""

                    async for event in runner.run_live(
                        user_id=client_id,
                        session_id=session.id,
                        live_request_queue=live_request_queue,
                        run_config=run_config,
                    ):
                        is_partial = getattr(event, "partial", True)

                        # Audio output
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                                    await websocket.send_bytes(part.inline_data.data)

                        # Transcriptions — role: agent (cumulative buffer)
                        if event.output_transcription:
                            chunk = (getattr(event.output_transcription, "text", "") or "")
                            # Filter control characters (e.g. <ctrl46>) that native audio
                            # model sometimes emits after tool responses
                            chunk = re.sub(r'<ctrl\d+>', '', chunk)
                            if chunk and not chunk.strip().startswith("**"):
                                finished = not is_partial
                                if finished:
                                    # Final already contains full text from ADK — use as-is
                                    display_text = chunk.strip()
                                    agent_tx_buf = ""
                                else:
                                    agent_tx_buf += chunk
                                    display_text = agent_tx_buf.strip()
                                log.info("Clara%s: %s", "" if finished else " (partial)", display_text)
                                await websocket.send_text(json.dumps({
                                    "type": "transcript",
                                    "role": "agent",
                                    "text": display_text,
                                    "finished": finished,
                                }))

                        # Transcriptions — role: user (cumulative buffer)
                        if event.input_transcription:
                            chunk = (getattr(event.input_transcription, "text", "") or "")
                            if chunk:
                                finished = not is_partial
                                if finished:
                                    # Final already contains full text from ADK — use as-is
                                    display_text = chunk.strip()
                                    user_tx_buf = ""
                                else:
                                    user_tx_buf += chunk
                                    display_text = user_tx_buf.strip()
                                if display_text in HIDDEN_GREETING_PROMPT:
                                    if finished:
                                        user_tx_buf = ""
                                    continue
                                log.info("User%s: %s", "" if finished else " (partial)", display_text)
                                await websocket.send_text(json.dumps({
                                    "type": "transcript",
                                    "role": "user",
                                    "text": display_text,
                                    "finished": finished,
                                }))


                        # Turn complete
                        if event.turn_complete:
                            log.info("Turn complete")
                            user_tx_buf = ""
                            agent_tx_buf = ""
                            await websocket.send_text(json.dumps({"type": "turn_complete"}))
                    
                    # If we finish successfully, break the retry loop
                    break

                except Exception as e:
                    err_msg = str(e)
                    if any(code in err_msg for code in ("1007", "1008", "1011")) and attempt < max_attempts:
                        log.warning("Attempt %d failed (error %s). Retrying...", attempt, err_msg)
                        if "1007" in err_msg:
                            consecutive_1007 += 1
                        else:
                            consecutive_1007 = 0
                        await asyncio.sleep(0.5 * attempt)
                        continue
                    raise

        async def send_to_browser():
            log.info("Starting ADK run_live for session %s (history: %d)", 
                     session.id, len(session.events))
            try:
                # Initial hidden greeting trigger — ONLY on fresh sessions
                if not session.events:
                    log.info("Fresh session: sending proactive greeting trigger")
                    live_request_queue.send_content(
                        types.Content(parts=[types.Part(text=HIDDEN_GREETING_PROMPT)])
                    )
                await run_live_loop()
            except Exception as e:
                err_str = str(e)
                if "1000" in err_str:
                    log.info("Gemini Live connection closed normally.")
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
