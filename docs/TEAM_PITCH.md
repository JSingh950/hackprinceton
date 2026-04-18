# Team Alignment Pitch — Read to the Team

60 seconds at the start of the build. Gets everyone on the same page before code.

---

## The Pitch (read verbatim)

> We're building **Rewind**.
>
> A small wall-mounted device with a camera that watches a room. It never records video — our Pi extracts events on-device: "keys placed at 2:47 PM," "pill bottle picked up at 8:02 AM," "person walked past." Those events are stored locally, in kilobytes. Nothing leaves the device unless you ask a question.
>
> You walk up, press a button on the device, and talk to the laptop next to it: *"where did I leave my keys?"* It tells you. Or *"did I take my meds this morning?"* And it shows you — yes, at 8:02, you picked up the orange bottle and drank water.
>
> It's the consumer product that three years of CVPR episodic-memory research has been pointing at. Nobody has shipped it. We're going to ship it this weekend.
>
> **Main track: Healthcare** — med adherence, elderly memory, ADHD. Secondary: Hardware+AI ($500), Eragon ($Mac Mini for the proactive caregiver-alert agent), K2 Think V2 (reMarkables), Telora ($40k founder track).
>
> **Roles:**
> - **Sunghoo:** the whole CV stack on the Pi — YOLO + ByteTrack + action rules + events + SQLite. He owns the vision pipeline.
> - **Ariji:** the AI layer — LLM query engine with K2 primary and Claude failover, the proactive Eragon agent, the FastAPI server on the Pi.
> - **Jeeyan:** the frontend — Next.js command center on the laptop with live event timeline, query UI, and Web Speech API for voice in/out. The laptop's own mic and speaker handle all audio.
> - **Me:** hardware integration — SenseCAP LVGL firmware, Grove button/LED wiring, enclosure, demo script, pitch, submissions.
>
> **Key architectural call: no USB mic, no Echo Dot, no Nest Mini.** The laptop already sits next to the device as our command center. Its browser handles speech-to-text and text-to-speech via the Web Speech API — free, local, no setup, no Bluetooth flakiness.
>
> **Rules for the next 35 hours:**
> 1. No pivots. We ship Rewind or we ship nothing.
> 2. Tonight: no integration. Each of us ships our solo piece by 2 AM. We merge tomorrow morning.
> 3. If stuck more than 45 minutes, tap out and ask.
> 4. The 2-minute demo is the product. If it's not in the demo, don't build it.
>
> We good? Let's go.

---

## Anticipated Objections

**"A camera in the home — won't people freak out about privacy?"**
→ That's our strongest pitch. No video stored, ever. Only structured events plus a 128×72 blurred thumbnail per event, all on-device. We have a physical cardboard shutter over the lens wired to a Grove servo. The privacy story is the *product*.

**"Isn't this just Nest / Ring / another security camera?"**
→ Those stream video to the cloud continuously. Ours doesn't touch the network except at query time, and only sends event text — never pixels. Also none of them answer natural-language questions about the past in plain English.

**"What if my YOLO model misses an object during the demo?"**
→ We limit live demos to 5 rehearsed objects (phone, keys, pill bottle, water bottle, book) and tune thresholds on exactly those Saturday afternoon. Generalization comes in v2. The demo needs perfection on hero scenarios, not generalization.

**"What if K2 acts weird like at Yale?"**
→ Claude 4.7 Opus failover wired from day one. One env var flip. We still pitch K2 for the MBZUAI track, we're not betting the demo on it.

**"No 3D printer — does the hardware still feel premium?"**
→ A clean cardboard + matte-black enclosure beats a rushed print if we're intentional. The Hardware+AI prize is judged on integration (CV + physical interface + SenseCAP), not enclosure tech.

**"Why not an Echo Dot or Nest Mini for voice?"**
→ Both are closed devices. Using their mic/speaker programmatically requires Alexa/Google Skills — 10+ hours of work and sends user voice through Amazon/Google cloud, which kills our privacy pitch. Laptop speaker + laptop mic via Web Speech API gets us 95% of the UX with 0% of the integration risk.

**"Should we do a mobile app?"**
→ No new platform. Our Next.js dashboard is already responsive — if a judge asks, we pull out a phone, open the same URL over the hotspot, show it's mobile-ready. "Works on any device with a browser" is the answer.
