# The 2-Minute Demo — verbatim, for rehearsal

This is the pitch-critical script extracted from [`PROJECT.md`](./PROJECT.md) for quick access on demo day. Rehearse it ≥10×. Stopwatch it. Cut anything that runs over 1:55.

---

## Setup on the judging table

- **Rewind device** mounted on cardboard "wall" prop. Webcam visible top, SenseCAP on front, Grove button prominent.
- **Laptop** beside it, dashboard full-screen, speakers audible, mic ready.
- **Scene table** in front: pill bottle, keys (or remote), water bottle, a phone.
- **Stopwatch on your phone: 2:00 countdown.**

---

## Script

### [0:00–0:15] The hook

> "Quick question — where did you put your phone when you walked up here?"

*(They look around, laugh, find it.)*

> "Now imagine that was your 72-year-old mom. Or your kid's inhaler. Or you at 2 AM wondering if you took your meds. Rooms don't remember. They should."

### [0:15–0:45] The plant

*(Hand the judge a small object — a spoon, sticky note.)*

> "Put this anywhere on the table while I keep talking. Anywhere. Don't tell me."

*(They place it. You don't look.)*

> "Rewind mounts on a wall. Watches the room. But it never records video — our Pi extracts events on-device. 'Object placed at 2:47 PM.' 'Person walked past at 2:48.' 'Pill bottle picked up at 8:02 AM.' Only events get stored. A whole week in a few megabytes. Nothing leaves the device except at query time, and even then only text — never a single frame."

### [0:45–1:15] The reveal

*(Press the Grove button on the device. LED pulses blue. SenseCAP shows "listening" state.)*

*(Speak into the laptop:)* "Where did the judge put the object I handed them?"

*(SenseCAP switches to "thinking" spinner. 2-second pause.)*

*(Laptop speaker:* "On the right edge of the table, 52 seconds ago."*)*

*(Laptop shows blurred thumbnail with red circle around the spot; SenseCAP displays the answer text.)*

*(Judge walks over. Object is there. Reactions happen.)*

### [1:15–1:45] The real use case

> "Parlor trick aside — here's what Rewind actually does."

*(Click the "Did I take my medication today?" preset on the laptop.)*

*(Answer card + laptop voice:* "Yes, at 8:02 AM. You picked up the orange bottle from the table, opened it, and drank water. First time since yesterday morning."*)*

*(Then a red alert card slides in from the right:)*

> "⚠ Evening dose is 6 hours overdue. Draft caregiver text?"

*(You tap it; a drafted SMS appears — tactful, calm, factual, ready to send.)*

> "That's our Eragon agent reading the event log plus a calendar plus contacts, and taking real action. For every caregiver of an elderly parent, every parent of a kid with chronic illness, every neurodivergent adult who forgets to eat."

### [1:45–2:00] The close

> "The EMQA research problem — 'where did I leave my keys?' — has been sitting in CVPR proceedings for years. We're the consumer product it was always pointing at. Everything private-by-design: no video ever leaves the Pi, only event text. $80 of hardware. Every home with a forgetful human — that's our market. And it starts here."

*(Smile. Let questions come.)*

---

## Pre-flight checklist (5 min before judging)

- [ ] Pi booted, `capture.py` running, events streaming (check `/events` endpoint)
- [ ] Backend on port 8000 responding (`curl localhost:8000/events`)
- [ ] Frontend on Chrome, full screen, sound turned up
- [ ] SenseCAP showing idle breathing state (or phone-stand fallback loaded)
- [ ] Grove button wired, LED working
- [ ] Hero objects placed on scene table: phone, keys, pill bottle, water bottle, book
- [ ] `.env` has working `ANTHROPIC_API_KEY` (Claude failover must work)
- [ ] Stopwatch started, 2:00 countdown ready
- [ ] One teammate watching the WebSocket in browser devtools in case it drops mid-demo
