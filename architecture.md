# Waypoint — Architecture Diagram

Paste the Mermaid block below into https://mermaid.live to render and export as PNG.

---

```mermaid
flowchart TD
    subgraph Browser["🌐 Browser  —  Plain HTML / JS"]
        direction TB
        MIC["🎙️ Microphone\nAudioWorklet\nPCM 16kHz capture"]
        SPK["🔊 Speaker\nAudioContext\nPCM playback"]
        TXS["💬 Transcript panel\nStreaming user + agent text"]
        CARDS["📋 Research Panel\nCourse · Event · Scholarship\nKnowledge · Booking cards"]
        VIS["📷 Vision input\nImage / camera frame\nsent alongside audio"]
    end

    subgraph CloudRun["☁️ Google Cloud Run  —  FastAPI + Uvicorn"]
        direction TB
        WS["WebSocket Handler\n/ws/{client_id}"]
        RUNNER["ADK Runner\nInMemorySessionService\nper-connection session"]
        QUEUE["LiveRequestQueue\naudio · image · text"]
        TOOLS["8 ADK Tools\nsearch_courses\nget_course_detail\nrecommend_courses\nsearch_events\nsearch_knowledge\nsearch_scholarships\nbook_campus_tour\ndisplay_data"]
    end

    subgraph GCP["Google Cloud Platform"]
        GEMINI["Gemini Live API  —  Vertex AI\ngemini-live-2.5-flash-native-audio\nReal-time bidirectional audio stream\nNative function calling · Barge-in · Transcription"]
        DB["Cloud SQL\nPostgreSQL 16 + pgvector\ncourses · events · scholarships\nknowledge_docs · tour_bookings"]
        SM["Secret Manager\nDATABASE_URL"]
        AR["Artifact Registry\nDocker image"]
        CB["Cloud Build\ncloudbuild.yaml\nCI/CD pipeline"]
    end

    %% Audio path (user → Gemini)
    MIC -- "PCM audio\n16kHz frames" --> WS
    VIS -- "image/jpeg\nbase64 frame" --> WS
    WS --> RUNNER
    RUNNER --> QUEUE
    QUEUE -- "Gemini Live\nBIDI WebSocket" --> GEMINI

    %% Audio path (Gemini → user)
    GEMINI -- "PCM audio\nresponse" --> QUEUE
    QUEUE --> RUNNER
    RUNNER --> WS
    WS -- "audio bytes\n+ transcript" --> SPK
    WS --> TXS

    %% Tool execution path
    GEMINI -- "function_call\n{tool, args}" --> RUNNER
    RUNNER --> TOOLS
    TOOLS -- "SQL / pgvector\nquery" --> DB
    DB -- "rows" --> TOOLS

    %% Card side-channel
    TOOLS -- "display_data\ncard JSON" --> WS
    WS -- "WebSocket\ncard message" --> CARDS

    %% Infrastructure
    SM -. "DATABASE_URL\nat startup" .-> CloudRun
    CB -. "build + push" .-> AR
    AR -. "deploy" .-> CloudRun

    %% Styles
    classDef browser fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    classDef cloudrun fill:#1a3d2b,stroke:#22c55e,color:#e2e8f0
    classDef gcp fill:#3b2a1a,stroke:#f59e0b,color:#e2e8f0
    classDef gemini fill:#4a1d6b,stroke:#a855f7,color:#e2e8f0

    class MIC,SPK,TXS,CARDS,VIS browser
    class WS,RUNNER,QUEUE,TOOLS cloudrun
    class DB,SM,AR,CB gcp
    class GEMINI gemini
```

---

## Key flows to call out in the Devpost story

| Flow | Description |
|------|-------------|
| **Audio in** | Browser AudioWorklet captures mic at 16kHz PCM → WebSocket → LiveRequestQueue → Gemini Live BIDI stream |
| **Audio out** | Gemini streams PCM back → ADK Runner → WebSocket → Browser AudioContext plays in real time |
| **Tool execution** | Gemini emits `function_call` → ADK Routes to correct tool → Tool queries Cloud SQL via pgvector → Result returned to Gemini |
| **Card side-channel** | Tools call `display_data` → JSON sent directly over WebSocket → Browser renders structured card without waiting for Clara to finish speaking |
| **Vision input** | Browser captures image frame → sent as `image/jpeg` blob alongside audio via LiveRequestQueue → Gemini processes multimodally |
| **CI/CD** | `git push` → Cloud Build triggers → Docker image pushed to Artifact Registry → Cloud Run deploys new revision |
