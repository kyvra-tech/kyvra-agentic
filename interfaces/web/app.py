"""FastAPI web interface for the Kyvra pipeline.

Endpoints:
  GET  /health                         → liveness check
  GET  /report?module=tech             → full AI daily report
  GET  /update?module=tech             → fast scan (no LLM)
  GET  /breaking?module=tech           → spike items only
  GET  /topic?module=tech&q=openai     → topic-scoped AI report
  GET  /brief?module=tech              → 3-bullet shareable brief
  GET  /thread?module=tech             → 7-tweet Twitter thread
  GET  /newsletter?module=tech         → newsletter section
  GET  /script?module=tech             → TikTok/Reels script
  GET  /status?module=tech             → source health & item counts
  POST /chat                           → multi-turn chat with the module persona
  POST /voice                          → save a voice profile for an API user
  GET  /voice/{user_id}                → retrieve current voice profile

Auth: Bearer token via Authorization header (API_KEY env var).
      If API_KEY is not set the server starts in open mode (dev only).
"""

import logging
import os
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from agents.supervisor import SupervisorAgent, load_module
from agents.content_writer import chat_with_llm
import services.memory as memory

logger = logging.getLogger(__name__)

# ── Auth ──────────────────────────────────────────────────────────────────────

_API_KEY = os.getenv("API_KEY", "")
_bearer = HTTPBearer(auto_error=False)

AVAILABLE_MODULES = ["tech", "crypto", "vietnam", "indie"]


def _verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    if not _API_KEY:
        return  # open mode — no auth required
    if credentials is None or credentials.credentials != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Kyvra API",
    description="AI content intelligence pipeline — reports, threads, briefs, scripts.",
    version="1.0.0",
)


def _supervisor(module: str) -> SupervisorAgent:
    if module not in AVAILABLE_MODULES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown module '{module}'. Available: {AVAILABLE_MODULES}",
        )
    return SupervisorAgent(load_module(module))


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    module: str = "tech"
    message: str
    history: list[dict[str, str]] = []
    user_id: int | None = None


class VoiceRequest(BaseModel):
    user_id: int
    voice: str  # max 500 chars enforced below


class TextResponse(BaseModel):
    module: str
    result: str


class StatusResponse(BaseModel):
    module: str
    total_fetched: int
    top_score: int
    spikes: int
    sources: dict[str, Any]


class VoiceResponse(BaseModel):
    user_id: int
    voice: str | None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _module_param(module: str = Query("tech", description="Module: tech | crypto | vietnam | indie")) -> str:
    return module


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}


@app.get("/report", response_model=TextResponse, tags=["content"], dependencies=[Depends(_verify_token)])
async def report(module: str = Depends(_module_param)) -> TextResponse:
    """Full AI-written daily report."""
    sv = _supervisor(module)
    result = await sv.generate_report()
    return TextResponse(module=module, result=result)


@app.get("/update", tags=["signal"], dependencies=[Depends(_verify_token)])
async def update(module: str = Depends(_module_param)) -> dict:
    """Fast scan — top scored items, no LLM writing."""
    sv = _supervisor(module)
    ctx = await sv.quick_scan()
    items = [
        {
            "title": i.title,
            "url": i.url,
            "source": i.source,
            "confidence_score": i.confidence_score,
            "is_spike": i.is_spike,
            "published_at": i.published_at,
        }
        for i in ctx.top_items
    ]
    return {"module": module, "total_fetched": len(ctx.raw_items), "items": items}


@app.get("/breaking", tags=["signal"], dependencies=[Depends(_verify_token)])
async def breaking(module: str = Depends(_module_param)) -> dict:
    """Spike items only — viral X tweets and high-momentum signals."""
    sv = _supervisor(module)
    ctx = await sv.quick_scan()
    spikes = [
        {
            "title": i.title,
            "url": i.url,
            "source": i.source,
            "confidence_score": i.confidence_score,
            "published_at": i.published_at,
        }
        for i in ctx.scored_items if i.is_spike
    ]
    return {"module": module, "spikes": spikes}


@app.get("/topic", response_model=TextResponse, tags=["content"], dependencies=[Depends(_verify_token)])
async def topic(
    q: str = Query(..., description="Keyword to scope the report"),
    module: str = Depends(_module_param),
) -> TextResponse:
    """AI report scoped to a keyword."""
    q = q[:200].replace("\n", " ").strip()
    sv = _supervisor(module)
    result = await sv.generate_report_for_topic(q)
    return TextResponse(module=module, result=result)


@app.get("/brief", response_model=TextResponse, tags=["content"], dependencies=[Depends(_verify_token)])
async def brief(
    module: str = Depends(_module_param),
    user_id: int | None = Query(None, description="User ID for voice profile lookup"),
) -> TextResponse:
    """3-bullet shareable brief from today's top 3 stories."""
    sv = _supervisor(module)
    result = await sv.generate_brief(user_id=user_id)
    return TextResponse(module=module, result=result)


@app.get("/thread", response_model=TextResponse, tags=["content"], dependencies=[Depends(_verify_token)])
async def thread(
    module: str = Depends(_module_param),
    user_id: int | None = Query(None, description="User ID for voice profile lookup"),
) -> TextResponse:
    """7-tweet Twitter/X thread from today's top story."""
    sv = _supervisor(module)
    result = await sv.generate_thread(user_id=user_id)
    return TextResponse(module=module, result=result)


@app.get("/newsletter", response_model=TextResponse, tags=["content"], dependencies=[Depends(_verify_token)])
async def newsletter(
    module: str = Depends(_module_param),
    user_id: int | None = Query(None, description="User ID for voice profile lookup"),
) -> TextResponse:
    """Newsletter section from today's top story."""
    sv = _supervisor(module)
    result = await sv.generate_newsletter(user_id=user_id)
    return TextResponse(module=module, result=result)


@app.get("/script", response_model=TextResponse, tags=["content"], dependencies=[Depends(_verify_token)])
async def script(
    module: str = Depends(_module_param),
    user_id: int | None = Query(None, description="User ID for voice profile lookup"),
) -> TextResponse:
    """TikTok/Reels voiceover script from today's top story."""
    sv = _supervisor(module)
    result = await sv.generate_script(user_id=user_id)
    return TextResponse(module=module, result=result)


@app.get("/status", response_model=StatusResponse, tags=["meta"], dependencies=[Depends(_verify_token)])
async def pipeline_status(module: str = Depends(_module_param)) -> StatusResponse:
    """Source health: items fetched, top confidence score, spike count."""
    sv = _supervisor(module)
    s = await sv.get_status()
    return StatusResponse(
        module=s["module"],
        total_fetched=s["total_fetched"],
        top_score=s["top_score"],
        spikes=s["spikes"],
        sources=dict(s["sources"]),
    )


@app.post("/chat", response_model=TextResponse, tags=["chat"], dependencies=[Depends(_verify_token)])
async def chat(req: ChatRequest) -> TextResponse:
    """Multi-turn chat with the module's AI persona."""
    if req.module not in AVAILABLE_MODULES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown module '{req.module}'. Available: {AVAILABLE_MODULES}",
        )
    message = req.message[:500].replace("\n", " ").strip()
    system_prompt = load_module(req.module).get_chat_system_prompt()
    reply = await chat_with_llm(message, system_prompt, req.history[-20:])
    return TextResponse(module=req.module, result=reply)


@app.post("/voice", response_model=VoiceResponse, tags=["voice"], dependencies=[Depends(_verify_token)])
async def set_voice(req: VoiceRequest) -> VoiceResponse:
    """Save or clear a voice profile for a user ID."""
    voice = req.voice[:500].replace("\n", " ").strip()
    memory.save_voice_profile(req.user_id, voice)
    return VoiceResponse(user_id=req.user_id, voice=voice or None)


@app.get("/voice/{user_id}", response_model=VoiceResponse, tags=["voice"], dependencies=[Depends(_verify_token)])
async def get_voice(user_id: int) -> VoiceResponse:
    """Retrieve the current voice profile for a user ID."""
    voice = memory.get_voice_profile(user_id)
    return VoiceResponse(user_id=user_id, voice=voice)
