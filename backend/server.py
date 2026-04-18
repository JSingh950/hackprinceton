"""
Rewind — FastAPI server on the Pi (starter)
Owner: Ariji

Run:   uvicorn server:app --host 0.0.0.0 --port 8000
Deps:  fastapi, uvicorn, httpx, anthropic, python-dotenv

Exposes:
  GET  /events              - last N events (initial UI load)
  POST /query               - {"question": "..."} -> answer JSON
  POST /agent/check         - runs proactive agent, returns alerts
  WS   /ws/events           - broadcasts new events as capture.py adds them
  POST /internal/event_added - capture.py posts here to trigger WS broadcast
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import query as query_mod
import agent as agent_mod

app = FastAPI(title="Rewind API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path("rewind.db")
connected_clients: set[WebSocket] = set()

class QueryIn(BaseModel):
    question: str

class EventIn(BaseModel):
    id: int
    ts: float
    event_type: str
    object: str
    track_id: int | None = None
    thumb_path: str | None = None

@app.get("/events")
def get_events(limit: int = 80) -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, ts, event_type, object, track_id, thumb_path FROM events "
        "ORDER BY ts DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/query")
def post_query(body: QueryIn) -> dict[str, Any]:
    return query_mod.query(body.question)

@app.post("/agent/check")
def post_agent_check() -> list[dict[str, Any]]:
    return agent_mod.run()

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket) -> None:
    await ws.accept()
    connected_clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive pings
    except WebSocketDisconnect:
        connected_clients.discard(ws)

async def broadcast_event(event: dict[str, Any]) -> None:
    dead: list[WebSocket] = []
    for client in connected_clients:
        try:
            await client.send_text(json.dumps(event))
        except Exception:
            dead.append(client)
    for d in dead:
        connected_clients.discard(d)

@app.post("/internal/event_added")
async def internal_event_added(body: EventIn) -> dict[str, str]:
    await broadcast_event(body.model_dump())
    return {"status": "ok"}
