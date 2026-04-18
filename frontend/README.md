# Frontend — Rewind command center

**Owner: Jeeyan.** Next.js 14 (App Router) + TypeScript + Tailwind. Runs on a laptop next to the Rewind device — the laptop's own mic and speaker handle all audio via the Web Speech API.

---

## What "done" looks like by Friday 2 AM

- [ ] `npm run dev` serves the three-panel dashboard at `http://localhost:3000`.
- [ ] Live event timeline populates from a mock WebSocket (no real Pi required tonight).
- [ ] Query box accepts text input; Ask → renders an Answer card.
- [ ] Mic button is wired to Web Speech API (Chrome only). Transcribed text → auto-submit.
- [ ] TTS speaks the answer aloud through the laptop speaker.
- [ ] Visual style: dark, monospace timestamps, emerald accents. Startup-polished, not demo-hacky.

## Run

```bash
cd frontend
npm install
cp .env.local.example .env.local    # set NEXT_PUBLIC_REWIND_API to the Pi's IP
npm run dev                          # http://localhost:3000
```

Use **Chrome** for the demo — `SpeechRecognition` is Chrome/Edge only. Typed input works in everything as the primary fallback.

## Env

`.env.local`:

```
NEXT_PUBLIC_REWIND_API=http://localhost:8000     # local dev
# NEXT_PUBLIC_REWIND_API=http://pi.local:8000    # on venue WiFi
# NEXT_PUBLIC_REWIND_API=http://192.168.x.y:8000 # hotspot fallback
```

WebSocket URL is derived automatically: `API.replace("http","ws") + "/ws/events"`.

## Layout

```
app/
├── layout.tsx       # root HTML shell (dark body, metadata)
├── globals.css      # Tailwind directives
└── page.tsx         # the whole dashboard — one client component
```

Three-panel layout:

1. **Left** — live event stream (WebSocket subscription + initial fetch).
2. **Center** — query input (text + Mic + TTS replay button) and Answer card.
3. **Right (stacked below on mobile)** — proactive agent alerts.

## Backend contract (what you consume)

See [`../backend/README.md`](../backend/README.md#api-what-jeeyan-consumes). Types in `page.tsx`:

```ts
type EventRow = { id, ts, event_type, object, track_id?, thumb_path? };
type Answer   = { answer, confidence, event_ids, _model? };
type Alert    = { severity, title, body, suggested_action? };
```

## Voice I/O (Web Speech API)

- **STT:** `SpeechRecognition` (webkit-prefixed in Chrome). Single-shot, `continuous = false`, `interimResults = false`. On result → set question + fire `ask()`.
- **TTS:** `speechSynthesis` + `SpeechSynthesisUtterance`. Pre-load voice list on mount (Chrome loads voices async). Prefer natural voices (`Samantha`, `Jenny`, `Google US English`, `Microsoft Aria`).
- **Always call `speechSynthesis.cancel()`** before speaking a new utterance so replays don't queue.

## Demo-critical polish

- Empty states that don't look broken ("No events yet. Place something in view.").
- Loading state on Ask button (the `"…"` trick is fine).
- Preset query chips visible so a judge can click "Did I take my medication today?" without speaking.
- Shutter toggle in the header as a privacy affordance (even if it's visual only — matches the Grove servo on the device).

## Fallback: mobile web view

If the SenseCAP firmware doesn't ship (Ariji's fallback plan), this dashboard becomes the device's face via a phone stand. The layout already responds — test at ~375 px width once on Saturday. A stripped-down `/status` route can be added in 20 min if needed.
