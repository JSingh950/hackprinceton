"""
Rewind — Query engine (starter)
Owner: Jossue

Run:   python query.py "where did I leave my keys"
Deps:  anthropic, httpx, python-dotenv

Goal by 2 AM Friday: `query("where are my keys")` returns a coherent JSON answer
against a mock or real event log. K2 primary, Claude 4.7 failover from day one.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path("rewind.db")
RECENT_EVENTS_LIMIT = 80
K2_ENDPOINT = os.getenv("K2_ENDPOINT", "")
K2_API_KEY = os.getenv("K2_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are the reasoning layer of Rewind, an on-device \
episodic-memory system for a physical space. You receive a structured event log \
and a user query. Answer strictly from the log. Never invent events. Respond \
in JSON only: {"answer": string, "confidence": "high"|"medium"|"low", "event_ids": [int]}. \
Keep answers under 2 sentences, warm tone, include specific times. If the log \
doesn't contain the answer, say: "I didn't see that happen.\""""

@dataclass
class EventRow:
    id: int
    ts: float
    event_type: str
    object: str

def load_recent_events(db_path: Path = DB_PATH, limit: int = RECENT_EVENTS_LIMIT) -> list[EventRow]:
    if not db_path.exists():
        return _mock_events()
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, ts, event_type, object FROM events ORDER BY ts DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [EventRow(*r) for r in reversed(rows)]

def _mock_events() -> list[EventRow]:
    base = datetime.now().timestamp() - 3600 * 3
    return [
        EventRow(1, base + 120,  "object_placed",      "scissors"),   # pill bottle stand-in
        EventRow(2, base + 135,  "action_detected",    "drinking_cup"),
        EventRow(3, base + 900,  "object_picked_up",   "bottle"),
        EventRow(4, base + 1050, "object_placed",      "bottle"),
        EventRow(5, base + 2100, "object_picked_up",   "cell phone"),
        EventRow(6, base + 2400, "person_entered",     "person"),
        EventRow(7, base + 2460, "object_placed",      "remote"),     # keys stand-in
        EventRow(8, base + 2700, "person_left",        "person"),
    ]

def format_log(events: list[EventRow]) -> str:
    lines = []
    for e in events:
        tstr = datetime.fromtimestamp(e.ts).strftime("%H:%M:%S")
        lines.append(f"[id={e.id}] [{tstr}] {e.event_type}: {e.object}")
    return "\n".join(lines)

def call_k2(log_text: str, question: str) -> dict | None:
    if not (K2_ENDPOINT and K2_API_KEY):
        return None
    try:
        r = httpx.post(
            K2_ENDPOINT,
            json={
                "model": "k2-think-v2",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Event log:\n{log_text}\n\nQuery: {question}"},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            },
            headers={"Authorization": f"Bearer {K2_API_KEY}"},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as exc:
        print(f"[k2] failed, falling back: {exc}", file=sys.stderr)
        return None

def call_claude(log_text: str, question: str) -> dict:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Event log:\n{log_text}\n\nQuery: {question}"}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text").strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def query(question: str) -> dict:
    events = load_recent_events()
    log_text = format_log(events)

    result = call_k2(log_text, question)
    if result is not None:
        result["_model"] = "k2-think-v2"
        return result

    result = call_claude(log_text, question)
    result["_model"] = "claude-opus-4-7"
    return result

def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python query.py \"your question\"")
        sys.exit(1)
    question = " ".join(sys.argv[1:])
    print(json.dumps(query(question), indent=2))

if __name__ == "__main__":
    main()
