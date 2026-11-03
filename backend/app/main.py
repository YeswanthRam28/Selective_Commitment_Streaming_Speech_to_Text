import os
import json
import uuid
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from app.models.events import PolicyConfig, PolicyMode, HypothesisEvent
from app.core.session import TranscriptionSession
from app.adapters.mock_adapter import DeterministicMockRecognizer
from app.adapters.whisper_adapter import WhisperRecognizer
from app.metrics.evaluator import compute_wer

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

WHISPER_AVAILABLE = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Server startup initialization:
    Pre-loads Whisper model into GPU memory and performs warm-up pass
    so streaming speech recognition starts with ZERO cold-start delay.
    """
    print("\n" + "=" * 70)
    print("[Server Startup] INITIALIZING WHISPER STREAMING ASR SUBSYSTEM")
    print("=" * 70)
    if TORCH_AVAILABLE and torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[Hardware] GPU: {gpu_name} ({vram_gb:.2f} GB VRAM) - CUDA Active")
    else:
        print("[Hardware] CPU Execution Mode")

    try:
        WhisperRecognizer.preload()
        print("=" * 70)
        print("[Startup Complete] OPENAI WHISPER PRE-WARMED & READY FOR STREAMING")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"[Startup Preload Warning] Whisper warmup deferred: {e}\n")

    yield

app = FastAPI(
    title="Selective Commitment Streaming ASR API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    cuda_avail = torch.cuda.is_available() if TORCH_AVAILABLE else False
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else None
    return {
        "status": "healthy",
        "whisper_available": WHISPER_AVAILABLE,
        "cuda_available": cuda_avail,
        "gpu_name": gpu_name,
        "supported_policies": [m.value for m in PolicyMode]
    }

class ReplayRequest(BaseModel):
    policy_config: PolicyConfig
    reference_text: Optional[str] = "We are testing selective commitment in speech recognition."

@app.post("/api/replay")
async def run_replay(request: ReplayRequest):
    """
    Runs the deterministic mock script through the configured policy and returns
    metrics (latency, revisions, final WER).
    """
    session_id = f"replay_{uuid.uuid4().hex[:8]}"
    session = TranscriptionSession(session_id, request.policy_config)
    mock = DeterministicMockRecognizer(interval=0.0)
    await mock.start_session(session_id)

    events_log = []
    async for hyp_event in mock.receive_events():
        update = session.handle_hypothesis(hyp_event)
        events_log.append(update.model_dump())

    wer_res = compute_wer(request.reference_text, session.spans[-1].text if session.spans else "")
    if session.spans:
        full_text = " ".join(s.text for s in session.spans)
        wer_res = compute_wer(request.reference_text, full_text)

    return {
        "session_id": session_id,
        "policy_mode": request.policy_config.mode.value,
        "total_revisions": session.total_revisions,
        "total_committed": session.total_committed,
        "final_transcript": " ".join(s.text for s in session.spans),
        "wer_metrics": wer_res,
        "updates_count": len(events_log)
    }

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    session: Optional[TranscriptionSession] = None
    adapter = None
    worker_task: Optional[asyncio.Task] = None

    async def event_forwarder():
        try:
            async for hyp in adapter.receive_events():
                update = session.handle_hypothesis(hyp)
                await websocket.send_text(update.model_dump_json())
        except Exception:
            pass

    try:
        while True:
            try:
                message = await websocket.receive()
            except (WebSocketDisconnect, RuntimeError):
                break

            if message.get("type") == "websocket.disconnect":
                break

            if "text" in message:
                data = json.loads(message["text"])
                action = data.get("action")

                if action == "start":
                    provider = data.get("provider", "whisper")
                    policy_dict = data.get("policy_config", {})
                    config = PolicyConfig(**policy_dict)

                    session = TranscriptionSession(session_id, config)

                    if provider == "mock":
                        adapter = DeterministicMockRecognizer()
                    else:
                        adapter = WhisperRecognizer()

                    await adapter.start_session(session_id)
                    worker_task = asyncio.create_task(event_forwarder())

                    actual_provider = "mock" if isinstance(adapter, DeterministicMockRecognizer) else "whisper"
                    await websocket.send_json({
                        "type": "session_started",
                        "session_id": session_id,
                        "provider": actual_provider,
                        "policy_mode": config.mode.value
                    })

                elif action == "stop":
                    if adapter:
                        await adapter.end_session()
                    if worker_task:
                        await worker_task
                    break

            elif "bytes" in message and adapter:
                await adapter.send_audio(message["bytes"])

    except WebSocketDisconnect:
        pass
    finally:
        if adapter:
            await adapter.end_session()
        if worker_task and not worker_task.done():
            worker_task.cancel()
