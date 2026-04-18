# Pi — CV pipeline

**Owner: Sunghoo.** Everything in this folder runs on the Raspberry Pi 4B.

Your piece is the eyes of Rewind: capture frames at 5 fps, detect + persistently track hero objects, extract *events* (not video), and write them to SQLite + a FastAPI broadcast endpoint.

---

## What "done" looks like by Friday 2 AM

- [ ] Pi boots. Webcam captures @ 5 fps (`capture.py` prints frame ticks).
- [ ] YOLOv8-nano + ByteTrack emits persistent track IDs across frames.
- [ ] Event extractor writes to `rewind.db` (SQLite). You can `sqlite3 rewind.db "SELECT * FROM events"` and see clean rows.
- [ ] Blurred 128×72 thumbnails saved to `thumbs/` — no face ever legible.
- [ ] Hero objects tuned well enough that placing/picking up a **phone, bottle, cup, remote, book, scissors** each fires a clean event.
- [ ] No integration with the backend/frontend tonight — `broadcast_event()` failing silently (server offline) is fine. That's Saturday's problem.

## Run

```bash
cd pi
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python capture.py
# ^C to stop
```

On Pi OS Bookworm without a venv: append `--break-system-packages` to pip.

## Hero objects (COCO labels + confidence floors)

Defined in `capture.py` at `HERO_OBJECTS`. We use COCO stand-ins for objects COCO doesn't have:

| Demo object | COCO label | Notes |
|---|---|---|
| Keys | `remote` | Similar size/material; COCO has no "keys" class |
| Pill bottle | `scissors` | Tuned for the meds demo |
| Phone | `cell phone` | Native |
| Water bottle | `bottle` | Native |
| Cup | `cup` | Drinking-action trigger |
| Book | `book` | Native |
| Person | `person` | Drinking-action requires person + drink overlap |

**Tune Saturday afternoon in venue lighting on exactly these objects.** Generalization isn't needed — we need perfection on rehearsed objects.

## Event taxonomy (what the extractor emits)

| `event_type` | When it fires | Example `object` |
|---|---|---|
| `object_placed` | A tracked object is stably visible for ≥3 frames (~0.6s) | `bottle`, `remote` |
| `object_picked_up` | A previously-confirmed object disappears for ≥10 frames (~2s) | `scissors` |
| `person_entered` | A `person` track stably appears | `person` |
| `person_left` | A confirmed `person` track disappears | `person` |
| `action_detected` | Simple rule: person bbox + drink bbox overlap in upper third | `drinking_bottle`, `drinking_cup` |

Debounced 8 s on drinking so we don't spam the log.

## Integration contract (don't change without pinging Ariji)

`capture.py` writes each event to `rewind.db` then POSTs it to the backend so the dashboard sees it live:

```python
POST http://127.0.0.1:8000/internal/event_added
{ "id": 42, "ts": 1713..., "event_type": "object_placed",
  "object": "bottle", "track_id": 17, "thumb_path": "thumbs/....jpg" }
```

If the server is offline, `httpx.post(...)` swallows the exception and the loop keeps running. Events are still written to SQLite and will appear on the next `GET /events` fetch.

## Debugging

```bash
# Count events by type
sqlite3 rewind.db "SELECT event_type, COUNT(*) FROM events GROUP BY event_type;"

# Tail live events
sqlite3 rewind.db "SELECT * FROM events ORDER BY ts DESC LIMIT 10;"

# Check thumbs are being saved
ls -la thumbs/ | head
```

If YOLO predictions look wrong, log the raw detections in `main()` before the `HERO_OBJECTS` filter — the confidence floor is often the culprit.

## Known risks + fallbacks

- **Pi < 5 fps:** drop to 3 fps (`TARGET_FPS = 3`). The ambient use case doesn't need more.
- **Camera index 0 wrong:** try `CAMERA_INDEX = 1` or `2`. `v4l2-ctl --list-devices` will show you.
- **ByteTrack config missing:** `bytetrack.yaml` ships with ultralytics; if not found, `pip install --upgrade ultralytics`.
