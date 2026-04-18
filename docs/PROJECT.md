# Rewind

> **Your home has a memory. Just ask.**
>
> An ambient, wall-mounted camera node that remembers what happened in a room so you don't have to. Never stores video — only events. Answers questions like *"Where did I leave my keys?"*, *"Did I take my medication?"*, *"When did the delivery arrive?"* in natural language.

---

## 📌 CONTEXT FOR AI ASSISTANTS (READ THIS FIRST)

If you are an AI assistant (Claude, GPT, etc.) loading this file to help the team: **this document is the single source of truth for project vision, architecture, constraints, and timeline.** When asked for help, ground every answer in what's defined here. Do not re-propose the project direction — it's locked. Your job is to help us *execute* on Rewind.

Key context to internalize:
- This is a **HackPrinceton 2026** project, submission due **Sunday April 19, 8 AM**.
- Team committed after long ideation; **no more pivots**.
- Main track: **Best Healthcare Hack**. Secondary: Hardware+AI, Eragon, K2 Think, Telora, Overall.
- Team is 3 people. Roles in `§ Team & Roles`.
- Hardware is fixed (MLH kit, no 3D printer, no USB mic, no Arduino). Constraints in `§ Hardware & Constraints`.
- Smart speakers (Echo Dot / Nest Mini) are **not used** — laptop handles all audio.
- Academic grounding (Bärmann & Waibel 2022 "Where did I leave my keys?", Ego4D) is real — cite when pitching.

When giving advice, **prefer concrete, shippable actions over exploratory suggestions.**

---

## 🎯 The Problem

Every home, lab, and workspace has **invisible events** that matter:
- An elderly parent forgets whether they took their 10 AM blood pressure medication.
- An ADHD adult spends 20 minutes a day looking for their wallet, keys, or phone.
- A lab researcher can't remember if they added the reagent at step 4 before stepping away.
- A caregiver needs to know: did dad sit down for more than 6 hours today? Did he eat?

All of this is **episodic memory about physical space** — and humans are *bad* at it. Current AI is bad at it too: VLMs answer questions about the *present*, but nobody has shipped a consumer product that remembers *the past of your space* and lets you query it in natural language.

## ✨ The Solution: Rewind

A small wall-mounted hardware node with a camera, a Raspberry Pi brain, and an ambient SenseCAP display. It runs continuously, extracting **events** (not video) on-device:

```
[14:23:07] object_placed { id: 42, object: "keys", location: "kitchen_counter" }
[14:25:12] person_entered_frame
[14:31:44] object_picked_up { id: 17, object: "pill_bottle_orange", duration: 8s }
[14:31:59] action_detected { action: "drinking" }
```

These events live in a tiny local SQLite database (kilobytes per day) alongside **one low-resolution blurred thumbnail per event**. Raw video is **never saved**. This is the architectural feature that makes the privacy claim real, not marketing.

Query in natural language — typed, via the laptop's own microphone (Web Speech API in the browser), or via a Grove button on the device:

> **User (presses Grove button on wall device, speaks into laptop):** "Where did I leave my keys?"
> **Rewind (laptop speaker speaks + SenseCAP displays):** "On the kitchen counter, 47 minutes ago."

---

## 📚 Academic Grounding (cite this when pitching)

This problem has a name in the research literature: **Episodic Memory Question Answering (EMQA)**.

- **Bärmann & Waibel (2022), "Where did I leave my keys? — Episodic-Memory-Based Question Answering on Egocentric Videos"** (CVPRW). Introduced the EMQA task and QAEGO4D dataset. Called out that state-of-the-art in 2022 scored ~10% accuracy — the problem was considered hard.
- **Grauman et al. (2021), "Ego4D: Around the World in 3,000 Hours of Egocentric Video"** — the NLQ (Natural Language Queries) task is exactly "where did I leave my X."
- **Why this matters now:** modern VLMs (Claude Opus 4.7, K2 Think V2) crush 2022 baselines. The research capability has caught up. Nobody has *productized* it as consumer hardware. That's the gap Rewind fills.

**Pitch line for judges:** *"The EMQA research problem has been sitting in CVPR proceedings for years. We're shipping the consumer product it was always pointing at."*

---

## 👥 Team & Roles

| Member | Background | Role in Rewind |
|---|---|---|
| **[You] (Jossue)** | Team lead, hackathon vet | **LLM & agent layer + Product + Pitch.** Query engine with K2 + Claude failover, Eragon proactive agent, FastAPI server on Pi. Also Devpost, demo script, track submissions. |
| **Ariji Chakma** | CS researcher at Drexel (2D/3D/4D gen, LLMs, HCI) | **Hardware integration.** SenseCAP LVGL firmware, Grove button/LED wiring, cardboard enclosure, privacy-shutter servo, MLH hardware pickup. |
| **Sunghoo Jung** | Rutgers, Math+CS, Rail Lab (edge ML, fault-tolerant ML, ResNet, real-time safety-critical systems) | **Computer vision stack.** Full CV pipeline: YOLOv8 detection + ByteTrack object persistence + simple action recognition rules + event extractor + SQLite log. He owns the Pi brain. |
| **Jeeyan** | Frontend | **Frontend + UX.** Next.js command center, live event timeline, query interface (text + Web Speech API for voice), answer card + TTS playback, demo visuals. |

> Kaijie is no longer on the team — his original LLM scope initially went to Ariji, and has since been swapped so Jossue owns the LLM/backend layer and Ariji owns the hardware integration.

---

## 🏆 Track Strategy (Prize Stack)

One build aimed at 5–7 prizes. Alignment is natural, not forced.

| Track | Why Rewind Wins | Prize |
|---|---|---|
| **Best Healthcare Hack** (main) | Medication adherence + elderly memory + ADHD assistance. Clinically real. | **Apple Watch Series 11 × team** |
| **Best Hardware+AI** (Justin Bojarski) | Real edge compute pipeline: YOLO + ByteTrack + action recognition on Pi. Physical device + SenseCAP + Grove button. | **$500** |
| **Build What Actually Runs Monday** (Eragon) | Agent reads event log + mock calendar + contacts, takes real action (drafts caregiver SMS when med missed). Multi-source, takes action, not summaries. | **Mac Mini** |
| **Best Use of K2 Think V2** (MBZUAI) | Temporal reasoning over structured event logs is K2's home turf. Multi-step deductions ("when did X last happen given Y and Z"). | **4× reMarkable tablets** |
| **Telora Startup Track** | Aging-in-place market is $500B+. Frontier research angle. Strong founder pitch. | **$40k founder funding** |
| **Best Overall** (auto-entered) | Undeniable demo + academic credibility + universal pain + privacy-first architecture. | **PlayStation 5 × team** |
| **Regeneron Clinical Trials** (stretch) | "Rewind for patient adherence monitoring in decentralized clinical trials" — worth a paragraph in Devpost. | **$2k pool** |

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────┐
│              REWIND DEVICE (wall-mounted)                │
│                                                          │
│   ┌──────────────┐         ┌──────────────────────┐      │
│   │  Logitech    │         │  SenseCAP Indicator   │     │
│   │  Webcam      │         │  (LVGL custom UI)     │     │
│   │  + cardboard │         │  - idle: breathing    │     │
│   │    shutter   │         │  - listening: pulse   │     │
│   └──────┬───────┘         │  - thinking: spinner  │     │
│          │ USB              │  - answer: wrapped   │     │
│          ▼                  │    text (15s)         │     │
│   ┌───────────────────────┐ └─────────┬────────────┘     │
│   │  Raspberry Pi 4B      │           │ Serial (USB)     │
│   │                       │───────────┘                  │
│   │  [Sunghoo]            │                              │
│   │  ├─ capture.py        │           ┌──────────────┐   │
│   │  │  @5fps OpenCV      │           │ Grove Button │   │
│   │  ├─ YOLOv8-nano       │◀─GPIO─────│  (wake/ask)  │   │
│   │  ├─ ByteTrack         │           └──────────────┘   │
│   │  │  (persistent IDs)  │                              │
│   │  ├─ action rules      │           ┌──────────────┐   │
│   │  │  (picked_up,       │──GPIO────▶│ Grove LED    │   │
│   │  │   drinking, etc.)  │           │  (status)    │   │
│   │  ├─ SQLite event log  │           └──────────────┘   │
│   │  └─ blurred 128×72    │                              │
│   │     thumbnails        │                              │
│   │                       │                              │
│   │  [Jossue]             │                              │
│   │  ├─ FastAPI server    │                              │
│   │  ├─ WS /ws/events     │                              │
│   │  ├─ POST /query       │                              │
│   │  │  → K2 Think V2     │                              │
│   │  │    (Claude 4.7     │                              │
│   │  │     failover)      │                              │
│   │  └─ POST /agent/check │                              │
│   │     (Eragon agent)    │                              │
│   └─────────┬─────────────┘                              │
└─────────────│────────────────────────────────────────────┘
              │ WiFi
              ▼
┌───────────────────────────────────────────────────────────┐
│  LAPTOP — Command Center + Audio I/O                      │
│  [Jeeyan]                                                 │
│                                                           │
│  Next.js + Tailwind + Web Speech API (browser-native):    │
│  ┌──────────────────┐  ┌─────────────────────────────┐    │
│  │ Live event       │  │ Query box                   │    │
│  │ timeline         │  │ (text input + mic button    │    │
│  │ (WebSocket)      │  │  that uses laptop's own mic │    │
│  └──────────────────┘  │  via Web Speech API)        │    │
│                        └─────────────────────────────┘    │
│  ┌──────────────────┐  ┌─────────────────────────────┐    │
│  │ Answer card      │  │ Proactive agent alerts      │    │
│  │ + TTS plays      │  │ (drafted caregiver SMS)     │    │
│  │   via laptop     │  └─────────────────────────────┘    │
│  │   speaker        │                                     │
│  └──────────────────┘                                     │
│                                                           │
│  Browser handles: STT + TTS (Web Speech API, free, local) │
└───────────────────────────────────────────────────────────┘
              ▲
              │ HTTPS (query time only, text not video)
              │
┌───────────────────────────────────────────────────────────┐
│  Cloud (query-time reasoning only, never video)           │
│  - K2 Think V2 (primary, for MBZUAI track pitch)          │
│  - Claude 4.7 / Opus (failover + Eragon agent drafting)   │
└───────────────────────────────────────────────────────────┘
```

### Why this architecture

1. **Privacy is real, not marketing.** No video ever stored or transmitted. Events = text. Thumbnails = 128×72px, heavily blurred, local only. Cloud only sees event text.
2. **No audio hardware dependencies.** Web Speech API in the browser handles STT and TTS. No USB mic needed. No Bluetooth pairing to smart speakers. No PyAudio on the Pi. Every laptop has a mic and speaker.
3. **Physical device stays simple.** Pi does CV + events + API. SenseCAP does ambient display. Grove button is a tactile wake trigger. That's it.
4. **Graceful degradation.** If voice input glitches → user types. If K2 glitches → Claude takes over. If SenseCAP firmware fails → phone-stand fallback. If WiFi flakes → local hotspot. Every layer has a fallback.

---

## 🔧 Hardware & Constraints

### What We Have (Confirmed)
- 1× Raspberry Pi 4B Kit (SD card, power, HDMI)
- 1× Logitech Webcam (USB)
- 1× SenseCAP Indicator (ESP32, we flash custom LVGL firmware)
- 1× Arduino Base Shield (we plug into Pi's GPIO via Grove HAT; no Arduino board needed)
- Grove buttons, Grove LEDs, Grove cables
- Breadboard + jumpers
- Both team laptops (for Jeeyan's dashboard + voice I/O)

### What We Don't Have (Adapt)
- ❌ **3D printer** — cardboard/matte-black enclosure instead. Clean design beats rushed print.
- ❌ **USB mic** — laptop mic via Web Speech API instead. Actually cleaner.
- ❌ **Arduino Uno/Nano** — don't need it. Pi 4B has 40 GPIO pins. Grove HAT plugs directly onto Pi.

### Ignored (on purpose)
- **Echo Dot / Nest Mini** — available but skipped. Using them for audio in/out requires either Alexa/Google Skills (10+ hour cloud rabbit hole, breaks privacy pitch) or flaky Bluetooth A2DP pairing. Laptop speaker/mic is simpler, more reliable. If we need visual "smart home" vibe on the demo table, we can set one down as a silent prop and mention in the pitch that Rewind would integrate with existing smart-home speakers as a future extension.

### Pi Performance Budget
- **5 fps** frame processing target — plenty for an ambient sensor.
- YOLOv8-nano: ~5–7 fps on Pi 4B CPU. Good.
- ByteTrack adds negligible overhead on top of YOLO (runs on already-detected boxes).
- Action rules are CPU-trivial (state deltas).
- SQLite + thumbnails = <50 MB/day.

---

## 🎬 The 2-Minute Demo (REHEARSE VERBATIM)

### Setup on the judging table
- **Rewind device** mounted on cardboard "wall" prop. Webcam visible top, SenseCAP on front, Grove button prominent.
- **Laptop** beside it, dashboard full-screen, speakers audible, mic ready.
- **Scene table** in front: pill bottle, keys (or remote), water bottle, a phone.
- **Stopwatch on your phone: 2:00 countdown.**

### Script

**[0:00–0:15] The hook.**
> "Quick question — where did you put your phone when you walked up here?"
*(They look around, laugh, find it.)*
> "Now imagine that was your 72-year-old mom. Or your kid's inhaler. Or you at 2 AM wondering if you took your meds. Rooms don't remember. They should."

**[0:15–0:45] The plant.**
*(Hand the judge a small object — a spoon, sticky note.)*
> "Put this anywhere on the table while I keep talking. Anywhere. Don't tell me."
*(They place it. You don't look.)*
> "Rewind mounts on a wall. Watches the room. But it never records video — our Pi extracts events on-device. 'Object placed at 2:47 PM.' 'Person walked past at 2:48.' 'Pill bottle picked up at 8:02 AM.' Only events get stored. A whole week in a few megabytes. Nothing leaves the device except at query time, and even then only text — never a single frame."

**[0:45–1:15] The reveal.**
*(Press the Grove button on the device. LED pulses blue. SenseCAP shows "listening" state.)*
*(Speak into the laptop:)* "Where did the judge put the object I handed them?"
*(SenseCAP switches to "thinking" spinner. 2-second pause.)*
*(Laptop speaker:* "On the right edge of the table, 52 seconds ago."*)*
*(Laptop shows blurred thumbnail with red circle around the spot; SenseCAP displays the answer text.)*
*(Judge walks over. Object is there. Reactions happen.)*

**[1:15–1:45] The real use case.**
> "Parlor trick aside — here's what Rewind actually does."
*(Click the "Did I take my medication today?" preset on the laptop.)*
*(Answer card + laptop voice:* "Yes, at 8:02 AM. You picked up the orange bottle from the table, opened it, and drank water. First time since yesterday morning."*)*
*(Then a red alert card slides in from the right:)*
> "⚠ Evening dose is 6 hours overdue. Draft caregiver text?"
*(You tap it; a drafted SMS appears — tactful, calm, factual, ready to send.)*
> "That's our Eragon agent reading the event log plus a calendar plus contacts, and taking real action. For every caregiver of an elderly parent, every parent of a kid with chronic illness, every neurodivergent adult who forgets to eat."

**[1:45–2:00] The close.**
> "The EMQA research problem — 'where did I leave my keys?' — has been sitting in CVPR proceedings for years. We're the consumer product it was always pointing at. Everything private-by-design: no video ever leaves the Pi, only event text. $80 of hardware. Every home with a forgetful human — that's our market. And it starts here."

*(Smile. Let questions come.)*

---

## 🛠️ Tech Stack

### Pi (Sunghoo's territory)
- **OS:** Raspberry Pi OS 64-bit (Bookworm)
- **Python:** 3.11
- **Key packages:**
  - `opencv-python` — frame capture
  - `ultralytics>=8.1` — YOLOv8-nano + built-in ByteTrack (`model.track(...)`)
  - `sqlite3` (stdlib) — event log
  - `fastapi` + `uvicorn` — API server
  - `websockets` (via FastAPI) — live event stream to laptop
  - `pyserial` — talk to SenseCAP over USB
  - `gpiozero` — Grove button/LED via GPIO
- **No audio dependencies** — Pi doesn't handle audio. Saves ~4 hours of PyAudio hell.

### Cloud (Jossue's territory)
- **Primary LLM:** K2 Think V2 (for MBZUAI track pitch). Structured JSON output.
- **Failover LLM:** Claude 4.7 (`claude-opus-4-7`). Wired from day one. One env var flip.
- **Agent drafts:** Claude 4.7 (better at tactful SMS tone than K2).

### Laptop Frontend (Jeeyan's territory)
- **Framework:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Real-time:** native WebSocket client → Pi's `ws://` endpoint
- **Voice input:** `SpeechRecognition` Web API (Chrome built-in, zero setup, free)
- **Voice output:** `speechSynthesis` Web API (Chrome built-in, zero setup, free)
- **Visual style:** dark mode, monospace timestamps, emerald accents (think Linear.app)

### SenseCAP (Your territory)
- **Firmware:** ESP-IDF + LVGL, starting from Seeed's examples
- **Four UI states:** idle (breathing dot), listening (pulsing), thinking (spinner), answer (wrapped text, 15s auto-dismiss)
- **Communication:** USB serial, JSON-lines from Pi: `{"state": "answer", "text": "..."}`
- **Fallback if flashing eats >2 hours:** phone in a small stand showing a minimal mobile web view. Judges never know.

---

## 📅 Sprint Plan (~35 hours to submit as of ~9 PM Fri)

### Phase 0 — COMMIT (right now)
- [ ] Team reads this README together. Any objections → raise now, then lock.
- [ ] Create GitHub repo. Push this README as first commit.
- [ ] Dedicated Discord/Slack channel for Rewind. Pin this README link.

### Phase 1 — PROVE EACH PIECE (Fri 9 PM → Sat 2 AM, ~5 hrs)

**Rule: no integration with anyone else's code tonight. Solo pieces only.**

| Owner | Deliverable by 2 AM |
|---|---|
| **Sunghoo** | Pi boots. Webcam captures @5fps. YOLOv8-nano + ByteTrack giving persistent IDs. Event extractor emits clean JSON events to stdout + SQLite. Blurred thumbnails saved. Hero objects tuned: phone, bottle, cup, book, remote. |
| **Jossue** | `query.py` standalone: takes JSON event log + question, returns structured answer. Works against K2 (if endpoint ready) and Claude failover. Tested on 5 synthetic event logs. FastAPI skeleton running. Devpost draft started. |
| **Jeeyan** | Next.js scaffold running. Three-panel layout. Live event timeline driven by mock WebSocket. Answer card. Web Speech API integrated (mic button works in Chrome; TTS reads answer card aloud). Looks *startup-polished*. |
| **Ariji** | SenseCAP firmware flashed with 4-state UI. Grove button + LED wired to Pi via Grove HAT. Cardboard enclosure sketched and materials claimed. MLH hardware pickup done. |

### Phase 2 — FIRST FUSION (Sat 8 AM → 1 PM, ~5 hrs)

| Task | Owner |
|---|---|
| Sunghoo's SQLite events → Jeeyan's live timeline via WebSocket | Sunghoo + Jeeyan |
| Jeeyan's query input (voice or text) → backend query endpoint → answer card + TTS | Jossue + Jeeyan |
| Pi ↔ SenseCAP serial working (real events drive screen states) | Ariji + Sunghoo |
| Device assembled in enclosure, wall-mount works, looks clean | Ariji |
| **Checkpoint @ 1 PM:** judge places keys, presses Grove button, speaks into laptop, gets correct spoken answer + SenseCAP text. If yes → on track. If no → cut voice, fall back to typed-only, keep moving. | All |

### Phase 3 — HERO MOMENTS (Sat 1 PM → 7 PM, ~6 hrs)

- [ ] **Medication demo scenario** — pill-bottle + drinking-action tuned; "did I take my meds" answer polished.
- [ ] **Privacy shutter** — Grove servo + cardboard flap over lens; Pi detects closed state; SenseCAP goes dark.
- [ ] **Eragon proactive agent** — reads event log + mock calendar → generates overdue alert → drafts caregiver SMS via Claude. **Wins the Mac Mini.**
- [ ] **Second query demo** — "when did someone last come in?" temporal reasoning via K2.
- [ ] Dry-run full 2-minute demo with teammate acting as judge. Note every rough moment.

### Phase 4 — POLISH & RECORD (Sat 7 PM → Sun 1 AM, ~6 hrs)

- [ ] Visual polish pass on UI — animations, loading states, empty states.
- [ ] Record 2-min demo video (even if optional submission — shooting it surfaces bugs). Upload unlisted YouTube.
- [ ] Rehearse demo 10× with stopwatch. Cut anything over 1:55.
- [ ] Devpost submission written — problem, solution, tech, academic grounding, future work.
- [ ] GitHub cleanup — README, setup instructions, architecture diagram, license.

### Phase 5 — SHIP (Sun 1 AM → 8 AM)

- [ ] **Sleep in shifts. Do not all-nighter.** Demos suffer badly without sleep.
- [ ] 4 AM: full dress rehearsal.
- [ ] 6 AM: Devpost submitted, GitHub finalized, video linked.
- [ ] **8 AM: submit.** Breakfast. 5× more rehearsal before 9:30 judging.

---

## 🚩 Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| YOLO mis-classifies a hero object during live demo | Limit demo to 5 rehearsed objects (phone, keys, bottle, pill bottle, book). Tune thresholds Saturday afternoon on exactly those objects. Rehearse in the judging venue's lighting if possible. |
| K2 returns malformed JSON mid-demo | Claude 4.7 failover wired day one. One env var flip. Also pitch K2 pragmatically — "We use K2 primary for multi-step temporal reasoning; Claude as production-grade failover." |
| Web Speech API doesn't work on judge's preferred browser | Typed input always visible as primary. Mic button is secondary. Demo works identically with typed input. |
| Pi-to-laptop WebSocket drops over venue WiFi | Create phone hotspot, both Pi and laptop join it. Dashboard can also run 100% local against `ws://pi.local:8000`. |
| SenseCAP firmware flash hell | Time-box to 2 hours Friday night. Fallback: phone-stand showing mobile web view of device state. |
| Team scope creep at 3 AM | This README is the veto document. Anything not listed = out of scope unless all 4 agree. |

---

## 🧠 Prompt Template (for Jossue)

### System prompt
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

### Sample interaction
```
Event log (last 4 hours):
[id=1] [08:02:14] object_picked_up: pill_bottle_orange, duration 11s
[id=2] [08:02:31] action_detected: drinking
[id=3] [08:15:02] object_placed: keys, location: kitchen_counter
[id=4] [10:47:33] person_entered_frame
[id=5] [10:48:01] object_picked_up: keys
...

Query: "Where are my keys?"

Expected JSON:
{
  "answer": "You picked them up from the kitchen counter at 10:48 AM — about 20 minutes ago. I haven't seen you set them down since.",
  "confidence": "high",
  "event_ids": [3, 5]
}
```

---

## 📝 Devpost Submission Checklist

- [ ] **Title:** Rewind — Ambient Memory for Your Space
- [ ] **Tagline:** "Your home has a memory. Just ask."
- [ ] **Problem** (1 paragraph, from above)
- [ ] **Solution** (2 paragraphs)
- [ ] **How we built it** (architecture + tech stack summary)
- [ ] **Academic grounding** (cite Bärmann & Waibel 2022 + Ego4D)
- [ ] **Challenges**
- [ ] **Accomplishments**
- [ ] **What's next:** wearable Ego4D-style form factor; clinical trial pilot (Regeneron); smart-home speaker integration (Alexa/Google); responsive mobile PWA (dashboard already works on phone)
- [ ] **GitHub link**
- [ ] **YouTube demo link** (optional but recommended)
- [ ] **Tracks selected:**
  - Main: Best Healthcare Hack ✅
  - Special: Best Hardware+AI (Bojarski), Eragon, K2 Think V2, Telora Startup
  - Stretch: Regeneron Clinical Trials (one paragraph in description)

---

## 📎 References

- Bärmann & Waibel 2022: "Where did I leave my keys? — Episodic-Memory-Based Question Answering on Egocentric Videos" (CVPRW). EMQA task + QAEGO4D dataset.
- Grauman et al. 2021: "Ego4D: Around the World in 3,000 Hours of Egocentric Video". NLQ benchmark.
- Meta V-JEPA 2 (2025): video world models with temporal memory.
- Google Project Astra: demos of long-context VLMs answering EMQA-style queries.
- Web Speech API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API (free browser STT + TTS)
- Ultralytics ByteTrack: https://docs.ultralytics.com/modes/track/
- SenseCAP LVGL examples: https://github.com/Seeed-Studio/sensecap-indicator-examples

---

## 🔒 Final Commitment

This README is the team's contract with itself. From this point forward:

1. **No pivots.** The idea is Rewind. We ship Rewind or we ship nothing.
2. **No scope creep.** Anything not in `§ Sprint Plan` requires unanimous team agreement.
3. **If stuck more than 45 minutes → ask.** Either a teammate or an AI assistant.
4. **The demo is the product.** If a feature doesn't appear in the 2-minute demo, it's not worth building.
5. **Ship by Sunday 8 AM.** Submitted-imperfect wins prizes. Unsubmitted-perfect wins nothing.

**Let's build something that outlasts the weekend.**
