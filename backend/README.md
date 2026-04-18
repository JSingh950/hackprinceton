# Backend — FastAPI + LLM layer

**Owner: Ariji.** FastAPI server running on the Raspberry Pi alongside `capture.py`. Handles the dashboard's reads, the LLM reasoning for queries, and the proactive caregiver agent.

---

## What "done" looks like by Friday 2 AM

- [ ] `query.py "where are my keys"` returns a valid JSON answer against the mock event log.
- [ ] K2 path tried first; Claude 4.7 failover works when K2 env vars are unset or endpoint flakes.
- [ ] FastAPI skeleton runs: `uvicorn server:app` → `http://localhost:8000/events` returns `[]` (or mock rows) without crashing.
- [ ] `/ws/events` accepts WS connections and doesn't drop them.
- [ ] You've tested against 5 synthetic event logs with hand-written questions (keys, meds, delivery, drinking, last-visit).
- [ ] No integration with Sunghoo's `capture.py` or Jeeyan's dashboard tonight.

## Files

| File | Purpose |
|---|---|
| `server.py` | FastAPI app — CORS, routes, WS broadcast |
| `query.py` | K2-primary / Claude-failover query engine. Standalone CLI too: `python query.py "..."` |
| `agent.py` | Eragon proactive agent — reads event log + mock calendar, drafts caregiver SMS via Claude |

## Run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # then fill in ANTHROPIC_API_KEY + K2_*
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Standalone query engine (no server required, runs against mock log if no DB):

```bash
python query.py "where did I leave my keys"
python query.py "did I take my medication today"
```

Run the agent check:

```bash
python agent.py
```

## API (what Jeeyan consumes)

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/events?limit=80` | — | `EventRow[]` |
| `POST` | `/query` | `{ "question": string }` | `{ answer, confidence, event_ids, _model }` |
| `POST` | `/agent/check` | — | `Alert[]` |
| `WS`   | `/ws/events` | (keepalive pings) | streams one `EventRow` per event |
| `POST` | `/internal/event_added` | `EventRow` | `{"status":"ok"}` — **Pi → Backend only** |

`EventRow`:

```ts
{
  id: number;
  ts: number;              // unix seconds
  event_type: string;
  object: string;
  track_id: number | null;
  thumb_path: string | null;
}
```

## System prompt (the contract with the LLM)

```
You are the reasoning layer of Rewind, an on-device episodic-memory system
for a physical space. You receive a structured event log and a user query.

Rules:
- Answer strictly from events in the log. Never invent events.
- Respond in JSON only: {"answer": string, "confidence": "high"|"medium"|"low", "event_ids": [int]}
- Keep answers under 2 sentences, warm tone, include specific times.
- If the log doesn't contain the answer, say: "I didn't see that happen."
- Never speculate about intent or emotion beyond what events show.
```

Already baked into `SYSTEM_PROMPT` in `query.py`. Don't drift from it without telling Jeeyan — the frontend assumes this exact JSON shape.

## Failover logic

`query.query(q)` calls `call_k2` first. Any exception (bad JSON, HTTP error, missing env vars) silently falls through to `call_claude`. Both return the same JSON schema; only `_model` differs. This is deliberate — one env var flip switches primary, and we never demo-fail on a flaky endpoint.

## Eragon agent (stretch — Saturday afternoon)

`agent.py` demonstrates the proactive caregiver alert:

1. Reads `events` from SQLite.
2. Compares against `MOCK_CALENDAR` (morning + evening meds).
3. If a dose window passed without a matching `object_picked_up` event on a pill-bottle-like object, creates an Alert.
4. For each alert, Claude drafts a 2-sentence SMS to the "caregiver" (`MOCK_CONTACTS`).

This wins the Eragon track because it's **multi-source** (events + calendar + contacts) and **takes action** (draft ready to send). Don't over-engineer — the demo needs *one* clean red alert card with a ready-to-send SMS draft.

## Debug / smoke tests

```bash
curl http://localhost:8000/events
curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' \
  -d '{"question":"where are my keys"}'
curl -X POST http://localhost:8000/agent/check
```

Or just hit `http://localhost:8000/docs` — FastAPI ships an interactive Swagger UI for free.
