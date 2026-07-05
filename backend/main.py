"""FastAPI app: create a debate, stream its events over SSE, replay stored state,
and serve the built frontend. One required env var: OPENROUTER_API_KEY.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import captcha, config, debate, personas, storage

app = FastAPI(title="The Roundtable")

# Dev convenience: Vite runs on :5173, backend on :8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory registry of pending debates (brief + rounds) keyed by id. The SSE GET
# actually runs the debate so EventSource (which can't POST a body) can drive it.
_PENDING: dict[str, dict] = {}

# Rolling timestamps of started debates, for the optional daily cap.
_STARTS: list[float] = []


def _gate_ok(supplied: str | None) -> bool:
    if not config.ACCESS_PHRASE:
        return True
    return captcha.normalize(supplied or "") == captcha.normalize(config.ACCESS_PHRASE)


def _cap_ok() -> bool:
    if config.DAILY_DEBATE_CAP <= 0:
        return True
    cutoff = time.time() - 86400
    _STARTS[:] = [t for t in _STARTS if t > cutoff]
    return len(_STARTS) < config.DAILY_DEBATE_CAP


class DebateRequest(BaseModel):
    brief: str = Field(min_length=1)
    rounds: int = Field(default=config.DEFAULT_ROUNDS, ge=1, le=6)


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "key_set": bool(config.OPENROUTER_API_KEY),
        "agent_model": config.AGENT_MODEL,
        "chairman_model": config.CHAIRMAN_MODEL,
        "gate": bool(config.ACCESS_PHRASE),
        "daily_cap": config.DAILY_DEBATE_CAP,
    }


@app.get("/api/agents")
async def agents():
    return {"agents": personas.public_agents()}


@app.get("/api/gate")
async def gate():
    """Tell the client whether a phrase is required, and if so the ASCII captcha to
    display. The phrase itself is never returned — only its rendered banner."""
    if not config.ACCESS_PHRASE:
        return {"required": False, "art": None}
    return {"required": True, "art": captcha.render(config.ACCESS_PHRASE)}


@app.post("/api/debate")
async def create_debate(
    req: DebateRequest, x_access_phrase: str | None = Header(default=None)
):
    if not _gate_ok(x_access_phrase):
        raise HTTPException(401, "Incorrect phrase — read the captcha and try again.")
    if not _cap_ok():
        raise HTTPException(429, "Daily debate limit reached. Try again tomorrow.")
    debate_id = uuid.uuid4().hex[:12]
    _PENDING[debate_id] = {"brief": req.brief, "rounds": req.rounds}
    _STARTS.append(time.time())
    return {"id": debate_id}


@app.get("/api/debate/{debate_id}/events")
async def stream_events(debate_id: str):
    pending = _PENDING.get(debate_id)
    if pending is None:
        raise HTTPException(404, "unknown or already-consumed debate id")

    async def gen():
        try:
            async for event in debate.run_debate(
                debate_id, pending["brief"], pending["rounds"]
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # flush
        finally:
            _PENDING.pop(debate_id, None)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/debate/{debate_id}")
async def get_debate(debate_id: str):
    record = storage.load(debate_id)
    if record is None:
        raise HTTPException(404, "no stored debate with that id")
    return record


@app.get("/api/debate/{debate_id}/transcript")
async def download_transcript(debate_id: str):
    """Server-rendered markdown transcript as a file download (nothing else is saved)."""
    record = storage.load(debate_id)
    if record is None:
        raise HTTPException(404, "no stored debate with that id")
    md = _render_markdown(record)
    return PlainTextResponse(
        md,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="roundtable-{debate_id}.md"'
        },
    )


def _render_markdown(record: dict) -> str:
    lines = ["# The Roundtable — Debate Transcript", ""]
    lines.append(f"**Brief:** {record.get('brief', '')}")
    lines.append("")
    last_round = None
    for t in record.get("transcript", []):
        if t.get("round") != last_round:
            last_round = t.get("round")
            lines += ["", f"## Round {last_round}", ""]
        lines.append(f"**{t.get('name')} · {t.get('role')}:** {t.get('text', '')}")
        lines.append("")
    verdict = record.get("verdict")
    if verdict:
        lines += ["", "## Verdict", "", verdict.get("text", ""), ""]
        for c in verdict.get("credits", []) or []:
            lines.append(f"- **{c.get('agent')}** — {c.get('argument')}")
    return "\n".join(lines) + "\n"


# --- Serve built frontend if present (production: single-command deploy) ---
_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="static")
