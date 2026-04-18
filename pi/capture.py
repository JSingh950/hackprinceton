"""
Rewind — Pi-side capture + tracking + event extraction (starter)
Owner: Sunghoo

Run:   python capture.py
Deps:  opencv-python, ultralytics, numpy, httpx

Goal by 2 AM Friday: this runs on the Pi, captures @5fps, YOLOv8-nano + ByteTrack
gives persistent IDs, event extractor emits clean events into SQLite, and pings
the FastAPI server so the laptop dashboard sees them live.
No integration with other people's code tonight. Solo piece.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import httpx
import numpy as np
from ultralytics import YOLO

# ---------- Config ---------------------------------------------------------

DB_PATH = Path("rewind.db")
THUMB_DIR = Path("thumbs")
THUMB_DIR.mkdir(exist_ok=True)
SERVER_BASE = "http://127.0.0.1:8000"  # Jossue's FastAPI

# Hero objects: YOLO COCO labels we care about, with per-label confidence floor.
# Tune Saturday on exactly these objects in venue lighting.
HERO_OBJECTS = {
    "cell phone": 0.40,
    "bottle": 0.45,
    "cup": 0.45,
    "remote": 0.40,        # stand-in for keys (COCO doesn't have "keys")
    "book": 0.45,
    "scissors": 0.45,      # stand-in for pill bottle
    "person": 0.50,
}

CAMERA_INDEX = 0
TARGET_FPS = 5
FRAME_W, FRAME_H = 640, 480
TRACKER_CFG = "bytetrack.yaml"   # ultralytics built-in

# ---------- Domain types ---------------------------------------------------

@dataclass
class TrackedDetection:
    track_id: int
    label: str
    conf: float
    bbox: tuple[int, int, int, int]

@dataclass
class Event:
    ts: float
    event_type: str
    object: str
    track_id: int | None
    bbox: tuple[int, int, int, int] | None
    thumb_path: str | None

# ---------- DB -------------------------------------------------------------

def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
      CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL NOT NULL,
        event_type TEXT NOT NULL,
        object TEXT NOT NULL,
        track_id INTEGER,
        bbox TEXT,
        thumb_path TEXT
      )
    """)
    conn.commit()
    return conn

def insert_event(conn: sqlite3.Connection, ev: Event) -> int:
    cur = conn.execute(
        "INSERT INTO events (ts, event_type, object, track_id, bbox, thumb_path) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (ev.ts, ev.event_type, ev.object, ev.track_id,
         str(ev.bbox) if ev.bbox else None, ev.thumb_path),
    )
    conn.commit()
    return cur.lastrowid

# ---------- Thumbnail (privacy-preserving) --------------------------------

def save_thumb(frame: np.ndarray, event_ts: float) -> str:
    # 128x72, heavy Gaussian blur, JPEG q=60 — no face ever legible
    small = cv2.resize(frame, (128, 72), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(small, (9, 9), 0)
    path = THUMB_DIR / f"{int(event_ts*1000)}.jpg"
    cv2.imwrite(str(path), blurred, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return str(path)

# ---------- Event extractor: track-based state machine --------------------

class EventExtractor:
    """
    Track-id-aware extractor. Handles appearance, disappearance, and simple
    action detection (drinking = person + bottle/cup near mouth region;
    holding = object + person bbox overlap over time).
    Simple, demo-safe, debuggable.
    """
    PRESENCE_FRAMES = 3     # ~0.6s @ 5fps
    ABSENCE_FRAMES = 10     # ~2s @ 5fps

    def __init__(self) -> None:
        # track_id -> label
        self.known_tracks: dict[int, str] = {}
        # track_id -> frames seen this round
        self.seen_count: dict[int, int] = {}
        # track_id -> frames missed since last seen
        self.miss_count: dict[int, int] = {}
        # track_id -> last known bbox
        self.last_bbox: dict[int, tuple[int,int,int,int]] = {}
        # track_ids we've confirmed as "placed/entered"
        self.confirmed: set[int] = set()
        # debounce drinking events so we don't spam
        self.last_drinking_ts: float = 0.0

    def step(self, detections: list[TrackedDetection]) -> list[Event]:
        events: list[Event] = []
        now = time.time()

        seen_ids = {d.track_id: d for d in detections}

        # Update presence counters for seen tracks
        for tid, det in seen_ids.items():
            self.known_tracks[tid] = det.label
            self.seen_count[tid] = self.seen_count.get(tid, 0) + 1
            self.miss_count[tid] = 0
            self.last_bbox[tid] = det.bbox
            if tid not in self.confirmed and self.seen_count[tid] >= self.PRESENCE_FRAMES:
                self.confirmed.add(tid)
                etype = "person_entered" if det.label == "person" else "object_placed"
                events.append(Event(now, etype, det.label, tid, det.bbox, None))

        # Update miss counters for confirmed tracks that disappeared
        for tid in list(self.confirmed):
            if tid not in seen_ids:
                self.miss_count[tid] = self.miss_count.get(tid, 0) + 1
                self.seen_count[tid] = 0
                if self.miss_count[tid] >= self.ABSENCE_FRAMES:
                    label = self.known_tracks.get(tid, "unknown")
                    etype = "person_left" if label == "person" else "object_picked_up"
                    events.append(Event(now, etype, label, tid, self.last_bbox.get(tid), None))
                    self.confirmed.discard(tid)

        # Simple action rule: drinking = person bbox + (bottle OR cup) bbox overlap in upper body
        events.extend(self._detect_drinking(detections, now))

        return events

    def _detect_drinking(self, detections: list[TrackedDetection], now: float) -> list[Event]:
        if now - self.last_drinking_ts < 8.0:  # debounce 8s
            return []
        person = next((d for d in detections if d.label == "person"), None)
        drink_obj = next((d for d in detections if d.label in ("bottle", "cup")), None)
        if person is None or drink_obj is None:
            return []
        # Upper third of person bbox
        px1, py1, px2, py2 = person.bbox
        upper_y = py1 + (py2 - py1) // 3
        dx1, dy1, dx2, dy2 = drink_obj.bbox
        dcy = (dy1 + dy2) // 2
        # Drink object center is in upper third AND horizontally within person bbox
        if py1 <= dcy <= upper_y and px1 <= (dx1 + dx2) // 2 <= px2:
            self.last_drinking_ts = now
            return [Event(now, "action_detected", f"drinking_{drink_obj.label}",
                         drink_obj.track_id, drink_obj.bbox, None)]
        return []

# ---------- Broadcast to FastAPI ------------------------------------------

def broadcast_event(event_id: int, ev: Event) -> None:
    """Non-blocking best-effort notify to FastAPI for WS broadcast."""
    try:
        httpx.post(
            f"{SERVER_BASE}/internal/event_added",
            json={
                "id": event_id,
                "ts": ev.ts,
                "event_type": ev.event_type,
                "object": ev.object,
                "track_id": ev.track_id,
                "thumb_path": ev.thumb_path,
            },
            timeout=0.5,
        )
    except Exception:
        pass  # server may be offline during Phase 1 testing

# ---------- Main loop ------------------------------------------------------

def main() -> None:
    print("[rewind] loading YOLOv8-nano...")
    model = YOLO("yolov8n.pt")

    print(f"[rewind] opening camera index {CAMERA_INDEX}...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    if not cap.isOpened():
        raise RuntimeError("camera failed to open — check lsusb and v4l permissions")

    conn = init_db()
    extractor = EventExtractor()
    frame_period = 1.0 / TARGET_FPS

    print("[rewind] running. Ctrl-C to quit.")
    try:
        while True:
            t0 = time.time()
            ok, frame = cap.read()
            if not ok:
                continue

            # Track mode: persistent IDs across frames (ByteTrack)
            results = model.track(frame, persist=True, tracker=TRACKER_CFG, verbose=False)[0]

            detections: list[TrackedDetection] = []
            if results.boxes is not None and results.boxes.id is not None:
                for box, tid in zip(results.boxes, results.boxes.id.int().tolist()):
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    if label not in HERO_OBJECTS:
                        continue
                    conf = float(box.conf[0])
                    if conf < HERO_OBJECTS[label]:
                        continue
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    detections.append(TrackedDetection(tid, label, conf, (x1, y1, x2, y2)))

            for ev in extractor.step(detections):
                # Save thumbnail if we have bbox + the frame is "interesting"
                if ev.event_type != "person_left":
                    ev.thumb_path = save_thumb(frame, ev.ts)
                event_id = insert_event(conn, ev)
                tstr = datetime.fromtimestamp(ev.ts).strftime("%H:%M:%S")
                print(f"[event {event_id}] {tstr} {ev.event_type:20s} "
                      f"{ev.object:20s} track={ev.track_id}")
                broadcast_event(event_id, ev)

            dt = time.time() - t0
            if dt < frame_period:
                time.sleep(frame_period - dt)

    except KeyboardInterrupt:
        print("[rewind] shutting down.")
    finally:
        cap.release()
        conn.close()

if __name__ == "__main__":
    main()
